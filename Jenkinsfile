pipeline {
    agent any
    environment {
        GIT_URL = 'https://github.com/Pandiarajan-Alwargandhi/imagebuild.git'
        DOCKER_IMAGE = 'artifactory.shs.saas.temenos.cloud:443/dockervirtual/testimages/hello-world-image'
        DOCKER_CREDENTIALS_ID = 'docker-registry-credentials-id'
        AZURE_CREDENTIALS_ID = 'git-repo-id'  // Replace with your Azure DevOps credentials ID
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
    }
    post {
        always {
            cleanWs()
        }
    }
}
