import os
import json
import time
import logging
import xml.etree.ElementTree as ET
from kubernetes import client, config, stream
from kubernetes.client.rest import ApiException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load externalized configuration files
def load_config_files():
    with open("/config/namespaces.json", "r") as ns_file:
        namespaces = json.load(ns_file)

    with open("/config/test_cases.json", "r") as test_file:
        test_cases = json.load(test_file)

    with open("/config/test_case_paths.json", "r") as paths_file:
        test_case_paths = json.load(paths_file)

    return namespaces, test_cases, test_case_paths

# Extract the app name from the namespace, handling cases with dynamically generated names like transact-159
def get_app_name_from_namespace(namespace):
    if "-" in namespace:
        return namespace.split("-")[0]  # Extracts 'transact' from 'transact-159'
    return namespace  # If no '-' found, return the namespace itself (for cases like 'transact')

# Dynamically fetch paths based on application
def get_app_paths(app_name, test_case_paths):
    return test_case_paths.get(app_name, {})

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
    timeout = 300
    check_interval = 5
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

def check_deployment_files(v1_api, namespace, pod_name, deployment_directory):
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

def substitute_namespace_in_url(url_template, namespace):
    if not url_template:
        return None
    return url_template.replace("{namespace}", namespace)

def perform_api_curl_on_pods(v1_api, namespace, app_paths):
    label_selector = app_paths.get("label_selector", "")
    api_curl_url_template = app_paths.get("api_curl_url", "")
    api_curl_url = substitute_namespace_in_url(api_curl_url_template, namespace)
    
    if not label_selector or not api_curl_url:
        logging.error("API curl test cannot proceed due to missing label_selector or api_curl_url.")
        return []

    try:
        api_response = v1_api.list_namespaced_pod(namespace, label_selector=label_selector)
        pods = api_response.items
        curl_results = []

        for pod in pods:
            pod_name = pod.metadata.name
            api_exec_command = [
                '/bin/sh',
                '-c',
                f'curl -v -s -w "%{{http_code}}" -o /dev/null {api_curl_url}'
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

def perform_web_curl_on_pods(v1_api, namespace, app_paths):
    label_selector = app_paths.get("label_selector", "")
    web_curl_url_template = app_paths.get("web_curl_url", "")
    web_curl_url = substitute_namespace_in_url(web_curl_url_template, namespace)
    web_username = app_paths.get("web_username", "")
    web_password = app_paths.get("web_password", "")
    
    if not label_selector or not web_curl_url:
        logging.error("Web curl test cannot proceed due to missing label_selector or web_curl_url.")
        return []

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

        errors = []
        with open("/tmp/pod_log_output.log", 'r') as file:
            for line in file:
                if 'error' in line.lower():
                    errors.append(line.strip())

        return errors if errors else []

    except ApiException as e:
        logging.error(f"Error executing command on pod {pod_name}: {e}")
        return [f"Error executing command: {e}"]

def calculate_test_results(report):
    total_tests = 0
    passed_tests = 0

    for namespace_report in report:
        tests = namespace_report["tests"]
        total_tests += len(tests)
        
        for pod in namespace_report["pods"]:
            for test in tests:
                if "check_pod_readiness" in test and all([pod.get("ready", False) for pod in namespace_report["pods"]]):
                    passed_tests += 1
                if "perform_api_curl_on_pods" in test and pod.get("api_curl_status", "000") == "200":
                    passed_tests += 1
                if "perform_web_curl_on_pods" in test and pod.get("web_curl_status", "000") == "200":
                    passed_tests += 1
                if "check_log_for_errors" in test and not pod.get("errors", []):
                    passed_tests += 1

    success_percentage = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    return total_tests, passed_tests, success_percentage

def generate_xml_report(report, total_tests, passed_tests, success_percentage):
    root = ET.Element("TestReport")
    tests_summary = ET.SubElement(root, "Summary")
    ET.SubElement(tests_summary, "TotalTests").text = str(total_tests)
    ET.SubElement(tests_summary, "PassedTests").text = str(passed_tests)
    ET.SubElement(tests_summary, "SuccessPercentage").text = f"{success_percentage:.2f}%"

    for namespace_report in report:
        namespace_element = ET.SubElement(root, "Namespace", name=namespace_report["namespace"])
        for pod in namespace_report["pods"]:
            pod_element = ET.SubElement(namespace_element, "Pod", name=pod["name"])
            for key, value in pod.items():
                if isinstance(value, list):
                    list_element = ET.SubElement(pod_element, key)
                    for item in value:
                        ET.SubElement(list_element, "Item").text = str(item)
                else:
                    ET.SubElement(pod_element, key).text = str(value)

    tree = ET.ElementTree(root)
    xml_report_path = "/tmp/test_report.xml"
    tree.write(xml_report_path)
    return xml_report_path

def main():
    load_k8s_config()
    v1_api = client.CoreV1Api()

    # Load the external config files
    namespaces, test_cases, test_case_paths = load_config_files()

    report = []
    for namespace in namespaces:
        # Extract app name from namespace
        app_name = get_app_name_from_namespace(namespace)
        
        app_paths = get_app_paths(app_name, test_case_paths)
        tests = test_cases.get(app_name, test_cases.get("default", []))
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
                pod_details["check_deployment_files"] = check_deployment_files(v1_api, namespace, pod.metadata.name, app_paths["deployment_directory"])
            if "perform_api_curl_on_pods" in tests and "api_curl_url" in app_paths:
                pod_details["perform_api_curl_on_pods"] = perform_api_curl_on_pods(v1_api, namespace, app_paths)
            if "perform_web_curl_on_pods" in tests and "web_curl_url" in app_paths:
                pod_details["perform_web_curl_on_pods"] = perform_web_curl_on_pods(v1_api, namespace, app_paths)
            if "check_log_for_errors" in tests:
                pod_details["check_log_for_errors"] = check_log_for_errors(v1_api, namespace, pod.metadata.name, app_paths["log_file_path"])

            namespace_report["pods"].append(pod_details)

        report.append(namespace_report)

    # Write the report to /tmp
    report_file_path = "/tmp/pod_test_results.json"
    with open(report_file_path, "w") as results_file:
        json.dump(report, results_file, indent=2)

    logging.info(f"Test results written to {report_file_path}")
    
    # Calculate test results and generate XML report
    total_tests, passed_tests, success_percentage = calculate_test_results(report)
    xml_report_path = generate_xml_report(report, total_tests, passed_tests, success_percentage)
    logging.info(f"XML Test Report: {xml_report_path}")

    # Print the test results to stdout
    if success_percentage < 100:
        logging.error(f"Tests failed with success percentage: {success_percentage}%")
        raise Exception("Test suite did not pass successfully.")

if __name__ == "__main__":
    main()
