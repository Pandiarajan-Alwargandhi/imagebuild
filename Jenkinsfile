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
        KUBE_CONFIG = credentials('aks-service-principal-credentials-id')
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
        stage('Create Namespace') {
            steps {
                script {
                    // Use Git Bash for the shell command
                    def namespaceExists = sh(script: "kubectl get namespace ${KUBE_NAMESPACE}", returnStatus: true, shell: 'bash')
                    if (namespaceExists != 0) {
                        sh "kubectl create namespace ${KUBE_NAMESPACE}", shell: 'bash'
                    } else {
                        echo "Namespace ${KUBE_NAMESPACE} already exists."
                    }
                }
            }
        }
        stage('Deploy to AKS') {
            steps {
                script {
                    // Use Git Bash for the shell command
                    sh '''
                        kubectl config use-context ${AKS_CLUSTER_NAME}
                        kubectl --kubeconfig=${KUBE_CONFIG} apply -f job.yaml -n ${KUBE_NAMESPACE}
                    ''', shell: 'bash'
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
