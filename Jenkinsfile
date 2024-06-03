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
        AZURE_CREDENTIALS_ID = 'aks-service-principal-credentials-id'  // Replace with your Azure DevOps credentials ID
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
        stage('Install Azure CLI and kubectl') {
            steps {
                bat '''
                REM Install Azure CLI if not already installed
                if not exist "%ProgramFiles(x86)%\\Microsoft SDKs\\Azure\\CLI2\\wbin" (
                    powershell -Command "Start-Process msiexec.exe -ArgumentList '/i https://aka.ms/installazurecliwindows.msi /quiet' -NoNewWindow -Wait"
                )

                REM Install kubectl
                az aks install-cli
                '''
            }
        }
        stage('Check AKS Cluster Availability') {
            steps {
                withCredentials([azureServicePrincipal(credentialsId: env.AZURE_CREDENTIALS_ID)]) {
                    script {
                        bat '''@echo off
                        REM Output the tenant ID for diagnostics
                        echo Tenant ID: %TENANT_ID%
                        echo AZURE_CLIENT_ID: %AZURE_CLIENT_ID%
                        echo AZURE_CLIENT_SECRET: %AZURE_CLIENT_SECRET%

                        REM Authenticate with Azure
                        az login --service-principal -u %AZURE_CLIENT_ID% -p %AZURE_CLIENT_SECRET% --tenant %TENANT_ID%

                        REM Account Set
                        az account set -s 154c599e-26ff-40dc-a4d4-f0bf217b5790

                        REM Check if AKS Cluster is available
                        az aks show --resource-group %RESOURCE_GROUP% --name %AKS_CLUSTER_NAME%
                        '''
                    }
                }
            }
        }
        stage('Get AKS Credentials') {
            steps {
                withCredentials([azureServicePrincipal(credentialsId: env.AZURE_CREDENTIALS_ID)]) {
                    script {
                        bat '''@echo off
                        REM Authenticate with Azure
                        az login --service-principal -u %AZURE_CLIENT_ID% -p %AZURE_CLIENT_SECRET% --tenant %TENANT_ID%

                        REM Get AKS credentials
                        az aks get-credentials --resource-group %RESOURCE_GROUP% --name %AKS_CLUSTER_NAME% --file %KUBECONFIG_FILE%
                        '''
                    }
                }
            }
        }
        stage('Deploy Job to AKS') {
            steps {
                withCredentials([azureServicePrincipal(credentialsId: env.AZURE_CREDENTIALS_ID)]) {
                    script {
                        bat '''@echo off
                        REM Authenticate with Azure
                        az login --service-principal -u %AZURE_CLIENT_ID% -p %AZURE_CLIENT_SECRET% --tenant %TENANT_ID%

                        REM Create Namespace if not exists
                        kubectl --kubeconfig=%KUBECONFIG_FILE% get namespace %KUBE_NAMESPACE% || kubectl --kubeconfig=%KUBECONFIG_FILE% create namespace %KUBE_NAMESPACE%

                        REM Deploy Job to AKS
                        kubectl --kubeconfig=%KUBECONFIG_FILE% apply -f job.yaml -n %KUBE_NAMESPACE%
                        '''
                    }
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
