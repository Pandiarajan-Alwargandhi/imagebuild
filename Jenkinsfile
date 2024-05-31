pipeline {
    agent any
    parameters {
        string(name: 'AKS_CLUSTER_NAME', defaultValue: '', description: 'Name of the AKS cluster')
        string(name: 'RESOURCE_GROUP', defaultValue: '', description: 'Name of the Azure resource group')
        string(name: 'TENANT_ID', defaultValue: '', description: 'Azure Tenant ID')
    }
    environment {
        GIT_URL = 'https://github.com/Pandiarajan-Alwargandhi/imagebuild.git'
        DOCKER_IMAGE = 'artifactory.shs.saas.temenos.cloud:443/dockervirtual/testimages/hello-world-image'
        DOCKER_CREDENTIALS_ID = 'docker-registry-credentials-id'
        AZURE_CREDENTIALS_ID = 'git-repo-id'  // Replace with your Azure DevOps credentials ID
        KUBE_NAMESPACE = 'sanitytest'
        KUBECONFIG_FILE = 'kubeconfig'
    }
    stages {
        stage('Checkout') {
            steps {
                git url: env.GIT_URL, credentialsId: env.AZURE_CREDENTIALS_ID
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${env.DOCKER_IMAGE}:${env.BUILD_NUMBER}")
                }
            }
        }
        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://artifactory.shs.saas.temenos.cloud:443', env.DOCKER_CREDENTIALS_ID) {
                        dockerImage.push("${env.BUILD_NUMBER}")
                    }
                }
            }
        }
        stage('Deploy to AKS') {
            steps {
                script {
                    sh '''#!/usr/bin/env python3
import subprocess

# Authenticate with Azure
subprocess.run(['az', 'login', '--service-principal', '-u', '$AZURE_CLIENT_ID', '-p', '$AZURE_CLIENT_SECRET', '--tenant', '$TENANT_ID'])

# Get AKS credentials
subprocess.run(['az', 'aks', 'get-credentials', '--resource-group', '$RESOURCE_GROUP', '--name', '$AKS_CLUSTER_NAME', '--file', '$KUBECONFIG_FILE'])

# Create Namespace if not exists
result = subprocess.run(['kubectl', '--kubeconfig=$KUBECONFIG_FILE', 'get', 'namespace', '$KUBE_NAMESPACE'], capture_output=True)
if result.returncode != 0:
    subprocess.run(['kubectl', '--kubeconfig=$KUBECONFIG_FILE', 'create', 'namespace', '$KUBE_NAMESPACE'])

# Deploy to AKS
subprocess.run(['kubectl', '--kubeconfig=$KUBECONFIG_FILE', 'apply', '-f', 'job.yaml', '-n', '$KUBE_NAMESPACE'])
'''
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}
