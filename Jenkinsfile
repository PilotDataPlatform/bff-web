pipeline {
    agent { label 'master' }
    environment {
      imagename_dev = "ghcr.io/pilotdataplatform/bff-web"
      imagename_staging = "ghcr.io/pilotdataplatform/bff-web"
      commit = sh(returnStdout: true, script: 'git describe --always').trim()
      registryCredential = 'pilot-ghcr'
      dockerImage = ''
    }

    stages {

    stage('Git clone for dev') {
        when {branch "develop"}
        steps{
          script {
              git branch: "develop",
              url: 'https://github.com/PilotDataPlatform/bff-web'
            }
        }
    }
    stage('DEV unit test') {
      when {branch "develop"}
      steps{
       withCredentials([
            string(credentialsId:'VAULT_TOKEN', variable: 'VAULT_TOKEN'),
            string(credentialsId:'VAULT_URL', variable: 'VAULT_URL'),
            file(credentialsId:'VAULT_CRT', variable: 'VAULT_CRT'),
            usernamePassword(credentialsId:'collabTestPass', usernameVariable: 'COLLAB_TEST_PASS_USERNAME', passwordVariable: 'COLLAB_TEST_PASS_PASSWORD')
          ]) {
            sh """
            pip install --user poetry==1.1.12
            ${HOME}/.local/bin/poetry config virtualenvs.in-project true
            ${HOME}/.local/bin/poetry install --no-root --no-interaction
            ${HOME}/.local/bin/poetry run pytest --verbose -c tests/pytest.ini
            """
        }
      }
    }

    stage('DEV Building and push image') {
      when {branch "develop"}
      steps{
        script {
          docker.withRegistry('https://ghcr.io', registryCredential) {
              customImage = docker.build("$imagename_dev:$commit", ".")
              customImage.push()
          }
        }
      }
    }

    stage('DEV Remove image') {
      when {branch "develop"}
      steps{
        sh "docker rmi $imagename_dev:$commit"
      }
    }

    stage('DEV Deploy bff') {
      when {branch "develop"}
      steps{
        build(job: "/VRE-IaC/UpdateAppVersion", parameters: [
          [$class: 'StringParameterValue', name: 'TF_TARGET_ENV', value: 'dev' ],
          [$class: 'StringParameterValue', name: 'TARGET_RELEASE', value: 'bff' ],
          [$class: 'StringParameterValue', name: 'NEW_APP_VERSION', value: "$commit" ]
        ])
      }
    }

    stage('Git clone staging') {
        when {branch "main"}
        steps{
          script {
              git branch: "main",
              url: 'https://github.com/PilotDataPlatform/bff-web'
            }
        }
    }

    stage('STAGING Building and push image') {
      when {branch "main"}
      steps{
        script {
            withCredentials([
              usernamePassword(credentialsId:'minio', usernameVariable: 'MINIO_USERNAME', passwordVariable: 'MINIO_PASSWORD')
            ]) {
                docker.withRegistry('https://ghcr.io', registryCredential) {
                    customImage = docker.build("imagename_staging:$commit", "--build-arg MINIO_USERNAME=$MINIO_USERNAME --build-arg MINIO_PASSWORD=$MINIO_PASSWORD .")
                    customImage.push()
                }
            }
        }
      }
    }

    stage('STAGING Remove bff image') {
      when {branch "main"}
      steps{
        sh "docker rmi $imagename_staging:$commit"
      }
    }

    stage('STAGING Deploy bff') {
      when {branch "main"}
      steps{
      build(job: "/VRE-IaC/Staging-UpdateAppVersion", parameters: [
        [$class: 'StringParameterValue', name: 'TF_TARGET_ENV', value: 'staging' ],
        [$class: 'StringParameterValue', name: 'TARGET_RELEASE', value: 'bff' ],
        [$class: 'StringParameterValue', name: 'NEW_APP_VERSION', value: "$commit" ]
      ])
      }
    }
  }
  post {
    failure {
        slackSend color: '#FF0000', message: "Build Failed! - ${env.JOB_NAME} commit_hash:$commit  (<${env.BUILD_URL}|Open>)", channel: 'jenkins-dev-staging-monitor'
    }
  }
}
