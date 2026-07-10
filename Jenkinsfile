pipeline {
    agent any

    parameters {
        choice(name: 'TEST_MARKER', choices: ['smoke', 'regression'], description: '本次业务测试范围')
    }

    environment {
        ENV = 'uat'
        REPORT_URL = "${env.BUILD_URL}allure"
    }

    stages {
        stage('安装依赖') {
            steps {
                sh 'python3 -m pip install -r requirements.txt -r requirements-dev.txt'
            }
        }

        stage('框架质量门禁') {
            steps {
                sh '''
                    python3 -m ruff format --check .
                    python3 -m ruff check .
                    PYTEST_ADDOPTS="--alluredir=reports/allure-framework --clean-alluredir --junitxml=reports/junit-framework.xml" python3 scripts/automation.py self-test
                '''
            }
        }

        stage('业务测试') {
            parallel {
                stage('接口测试') {
                    steps {
                        sh 'PYTEST_ADDOPTS="--alluredir=reports/allure-api --clean-alluredir --junitxml=reports/junit-api.xml" python3 scripts/automation.py test --type api --env uat --marker "${TEST_MARKER}"'
                    }
                }
                stage('Web测试') {
                    steps {
                        sh '''
                            python3 -m playwright install --with-deps chromium
                            PYTEST_ADDOPTS="--alluredir=reports/allure-web --clean-alluredir --junitxml=reports/junit-web.xml" python3 scripts/automation.py test --type web --env uat --marker "${TEST_MARKER}"
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit-*.xml'
            allure includeProperties: false, results: [
                [path: 'reports/allure-framework'],
                [path: 'reports/allure-api'],
                [path: 'reports/allure-web']
            ]
            withCredentials([
                string(credentialsId: 'DINGTALK_WEBHOOK', variable: 'DINGTALK_WEBHOOK'),
                string(credentialsId: 'DINGTALK_SECRET', variable: 'DINGTALK_SECRET'),
                string(credentialsId: 'WECOM_WEBHOOK', variable: 'WECOM_WEBHOOK'),
                string(credentialsId: 'SMTP_HOST', variable: 'SMTP_HOST'),
                string(credentialsId: 'SMTP_PORT', variable: 'SMTP_PORT'),
                string(credentialsId: 'SMTP_USER', variable: 'SMTP_USER'),
                string(credentialsId: 'SMTP_PASSWORD', variable: 'SMTP_PASSWORD'),
                string(credentialsId: 'EMAIL_TO', variable: 'EMAIL_TO')
            ]) {
                sh 'python3 scripts/notify_from_junit.py reports || true'
            }
        }
    }
}
