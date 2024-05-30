pipeline {
    agent any
    parameters {
        string(name: 'AKS_CLUSTER_NAME', defaultValue: '', description: 'Name of the AKS cluster')
        string(name: 'RESOURCE_GROUP', defaultValue: '', description: 'Name of the Azure resource group')
    }
    environment {
        GIT_URL = 'https://github.com/Pandiarajan-Alwargandhi/imagebuild.git'
        DOCKER_IMAGE = 'artifactory.shs.saas.temenos.cloud:443/dockervirtual/testimages/hello-world-image'
        DOCKER_CREDENTIALS_ID = 'docker-registry-credentials-id'
        AZURE_CREDENTIALS_ID = 'git-repo-id'  // Replace with your Azure DevOps credentials ID
        KUBE_NAMESPACE = 'sanitytest'
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
        stage('Authenticate with Azure') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'aks-service-principal-credentials-id', usernameVariable: 'AZURE_CLIENT_ID', passwordVariable: 'AZURE_CLIENT_SECRET')]) {
                    script {
                        bat '''
                            az login --service-principal -u %AZURE_CLIENT_ID% -p %AZURE_CLIENT_SECRET% --tenant YOUR_TENANT_ID
                            az aks get-credentials --resource-group %RESOURCE_GROUP% --name %AKS_CLUSTER_NAME% --file kubeconfig
                        '''
                    }
                }
            }
        }
        stage('Create Namespace') {
            steps {
                script {
                    // Check if namespace exists, create if not
                    def namespaceExists = bat(script: "kubectl --kubeconfig=kubeconfig get namespace %KUBE_NAMESPACE%", returnStatus: true)
                    if (namespaceExists != 0) {
                        bat "kubectl --kubeconfig=kubeconfig create namespace %KUBE_NAMESPACE%"
                    } else {
                        echo "Namespace ${env.KUBE_NAMESPACE} already exists."
                    }
                }
            }
        }
        stage('Deploy to AKS') {
            steps {
                script {
                    // Deploy to AKS
                    bat '''
                        kubectl --kubeconfig=kubeconfig apply -f job.yaml -n %KUBE_NAMESPACE%
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
