import os
import time
import json
import logging
from kubernetes import client, config, stream
from kubernetes.client.rest import ApiException

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

deployment_directory = "/opt/jboss/wildfly/standalone/deployments"
check_interval = 5
timeout = 300  # 5 minutes
app_label = "temenos-transact-app"
api_curl_url = "http://127.0.0.1:8080/irf-provider-container/api/v1.0.0/meta/apis"
log_file_path = "/opt/jboss/wildfly/standalone/log/server.log"

# Web URL and credentials
web_curl_url = "http://127.0.0.1:8080/transact-explorer-wa/#/login"
web_username = "INPUTT"
web_password = "123456"

def load_k8s_config():
    try:
        config.load_incluster_config()
    except Exception:
        try:
            config.load_kube_config()
        except Exception as e:
            logging.error(f"Failed to load kubeconfig: {e}")
            raise

def is_pod_ready(pod):
    conditions = pod.status.conditions
    for condition in conditions:
        if condition.type == "Ready" and condition.status == "True":
            return True
    return False

def get_pod_events(v1_api, namespace, pod_name):
    try:
        events = v1_api.list_namespaced_event(namespace, field_selector=f"involvedObject.name={pod_name}")
        event_details = []
        for event in events.items:
            event_details.append({
                "timestamp": str(event.last_timestamp),
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "source": event.source.component
            })
        return event_details
    except ApiException as e:
        logging.error(f"Error getting events for pod {pod_name}: {e}")
        return [{"error": str(e)}]

def check_pod_readiness(v1_api, namespace):
    end_time = time.time() + timeout
    namespace_status = {
        "namespace": namespace,
        "test_case": "check_pod_readiness",
        "pods": []
    }

    while time.time() < end_time:
        try:
            api_response = v1_api.list_namespaced_pod(namespace)
            pods = api_response.items
            all_ready = True

            for pod in pods:
                pod_name = pod.metadata.name
                ready = is_pod_ready(pod)
                pod_details = {
                    "name": pod_name,
                    "ready": ready,
                    "events": get_pod_events(v1_api, namespace, pod_name) if not ready else []
                }
                namespace_status["pods"].append(pod_details)
                if not ready:
                    all_ready = False

            if all_ready:
                return namespace_status

            time.sleep(check_interval)
        except ApiException as e:
            logging.error(f"Error listing pods in namespace {namespace}: {e}")
            return {"error": str(e)}

    for pod in namespace_status["pods"]:
        if not pod["ready"]:
            pod["events"] = get_pod_events(v1_api, namespace, pod["name"])
    return namespace_status

def check_deployment_files(v1_api, namespace, pod_name):
    exec_command = [
        '/bin/sh',
        '-c',
        f'ls -l {deployment_directory}/*.failed || echo "No deployment failed"'
    ]

    try:
        response = stream.stream(
            v1_api.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            command=exec_command,
            stderr=True, stdin=False,
            stdout=True, tty=False
        )

        if "No deployment failed" in response:
            return "All deployments succeeded"
        else:
            return f"Failed deployments:\n{response}"

    except ApiException as e:
        logging.error(f"Error executing command on pod {pod_name}: {e}")
        return f"Error executing command: {e}"

def perform_api_curl_on_pods(v1_api, namespace, label_selector):
    try:
        api_response = v1_api.list_namespaced_pod(namespace, label_selector=label_selector)
        pods = api_response.items
        curl_results = []

        for pod in pods:
            pod_name = pod.metadata.name
            api_exec_command = [
                '/bin/sh',
                '-c',
                f'curl -o /dev/null -s -w "%{{http_code}}" {api_curl_url}'
            ]

            try:
                api_response = stream.stream(
                    v1_api.connect_get_namespaced_pod_exec,
                    pod_name,
                    namespace,
                    command=api_exec_command,
                    stderr=True, stdin=False,
                    stdout=True, tty=False
                )

                curl_results.append({
                    "pod_name": pod_name,
                    "api_curl_status": api_response.strip()
                })

            except ApiException as e:
                logging.error(f"Error performing API curl on pod {pod_name}: {e}")
                curl_results.append({
                    "pod_name": pod_name,
                    "error": f"Error: {e}"
                })

        return curl_results

    except ApiException as e:
        logging.error(f"Error listing pods in namespace {namespace}: {e}")
        return [{"error": str(e)}]

def perform_web_curl_on_pods(v1_api, namespace, label_selector):
    try:
        api_response = v1_api.list_namespaced_pod(namespace, label_selector=label_selector)
        pods = api_response.items
        curl_results = []

        for pod in pods:
            pod_name = pod.metadata.name
            web_exec_command = [
                '/bin/sh',
                '-c',
                f'curl -o /dev/null -s -w "%{{http_code}}" -X POST -d "username={web_username}&password={web_password}" {web_curl_url}'
            ]

            try:
                web_response = stream.stream(
                    v1_api.connect_get_namespaced_pod_exec,
                    pod_name,
                    namespace,
                    command=web_exec_command,
                    stderr=True, stdin=False,
                    stdout=True, tty=False
                )

                curl_results.append({
                    "pod_name": pod_name,
                    "web_curl_status": web_response.strip()
                })

            except ApiException as e:
                logging.error(f"Error performing web curl on pod {pod_name}: {e}")
                curl_results.append({
                    "pod_name": pod_name,
                    "error": f"Error: {e}"
                })

        return curl_results

    except ApiException as e:
        logging.error(f"Error listing pods in namespace {namespace}: {e}")
        return [{"error": str(e)}]

def read_log_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    error_messages = []

    with open(file_path, 'r') as file:
        for line in file:
            if 'error' in line.lower():
                error_messages.append(line.strip())

    return error_messages

def check_log_for_errors(v1_api, namespace, pod_name, log_file_path):
    exec_command = [
        '/bin/sh',
        '-c',
        f'cat {log_file_path}'
    ]

    try:
        response = stream.stream(
            v1_api.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            command=exec_command,
            stderr=True, stdin=False,
            stdout=True, tty=False
        )

        with open("/tmp/pod_log_output.log", "w") as log_file:
            log_file.write(response)

        errors = read_log_file("/tmp/pod_log_output.log")
        if errors:
            return errors
        else:
            return []

    except ApiException as e:
        logging.error(f"Error executing command on pod {pod_name}: {e}")
        return [f"Error executing command: {e}"]

def main():
    load_k8s_config()
    v1_api = client.CoreV1Api()

    with open(os.getenv("CONFIG_PATH", "/config/tests_config.json"), "r") as config_file:
        tests_config = json.load(config_file)

    with open(os.getenv("NAMESPACES_PATH", "/config/namespaces.json"), "r") as ns_file:
        namespaces = json.load(ns_file)

    if "ALL" in namespaces:
        namespaces = [ns.metadata.name for ns in v1_api.list_namespace().items]

    report = []
    for namespace in namespaces:
        tests = tests_config.get(namespace, tests_config.get("default", []))
        namespace_report = {
            "namespace": namespace,
            "tests": tests,
            "pods": []
        }

        if "check_pod_readiness" in tests:
            pod_readiness = check_pod_readiness(v1_api, namespace)
            namespace_report["pods"].extend(pod_readiness["pods"])

        api_response = v1_api.list_namespaced_pod(namespace)
        for pod in api_response.items:
            pod_details = {
                "name": pod.metadata.name
            }
            if "check_deployment_files" in tests:
                pod_details["check_deployment_files"] = check_deployment_files(v1_api, namespace, pod.metadata.name)
            if "perform_api_curl_on_pods" in tests:
                pod_details["perform_api_curl_on_pods"] = perform_api_curl_on_pods(v1_api, namespace, f"app={app_label}")
            if "perform_web_curl_on_pods" in tests:
                pod_details["perform_web_curl_on_pods"] = perform_web_curl_on_pods(v1_api, namespace, f"app={app_label}")
            if "check_log_for_errors" in tests:
                pod_details["check_log_for_errors"] = check_log_for_errors(v1_api, namespace, pod.metadata.name, log_file_path)

            namespace_report["pods"].append(pod_details)

        report.append(namespace_report)

    # Modified path to write the report to /tmp, which is typically writable
    report_file_path = "/tmp/pod_test_results.json"
    with open(report_file_path, "w") as results_file:
        json.dump(report, results_file, indent=2)

    logging.info(f"Test results written to {report_file_path}")
    
    # Print the test results to stdout
    with open(report_file_path, "r") as results_file:
        report_data = results_file.read()
        logging.info(f"Test results: {report_data}")

if __name__ == "__main__":
    main()
