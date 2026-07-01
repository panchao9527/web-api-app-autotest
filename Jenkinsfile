// =====================================================================
// Jenkins 声明式流水线（与 GitHub Actions / GitLab CI 等价）
// 阶段: 安装依赖 -> 并行(接口+Web)测试 -> 汇总推送 + 归档报告
//
// 【使用前准备】
// 1. Jenkins 需装插件: Allure(展示报告)、HTML Publisher(可选)
// 2. 在 凭据(Credentials) 里添加 Secret text，ID 与下方一致：
//    TEST_USERNAME / TEST_PASSWORD / DINGTALK_WEBHOOK / WECOM_WEBHOOK
//    SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / EMAIL_TO
// 3. agent 需具备 python3/pip；Web 测试需能装 playwright 浏览器
// =====================================================================

pipeline {
    agent any

    environment {
        ENV = 'uat'
        // 报告地址：改成你 Jenkins 的 Allure 地址或公司报告地址
        REPORT_URL = "${env.BUILD_URL}allure"
    }

    stages {
        stage('安装依赖') {
            steps {
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('测试') {
            parallel {
                stage('接口测试') {
                    steps {
                        sh 'python3 -m pytest -m api --alluredir=reports/allure-results --junitxml=reports/junit-api.xml'
                    }
                }
                stage('Web测试') {
                    steps {
                        sh '''
                            python3 -m playwright install --with-deps chromium
                            python3 -m pytest -m web --alluredir=reports/allure-results --junitxml=reports/junit-web.xml
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            // 展示 junit 结果
            junit 'reports/junit-*.xml'

            // 生成/展示 Allure 报告(需 Allure Jenkins 插件)
            allure includeProperties: false, results: [[path: 'reports/allure-results']]

            // 汇总结果并推送钉钉/企微/邮件(凭据注入为环境变量)
            withCredentials([
                string(credentialsId: 'DINGTALK_WEBHOOK', variable: 'DINGTALK_WEBHOOK'),
                string(credentialsId: 'DINGTALK_SECRET',  variable: 'DINGTALK_SECRET'),
                string(credentialsId: 'WECOM_WEBHOOK',    variable: 'WECOM_WEBHOOK'),
                string(credentialsId: 'SMTP_HOST',        variable: 'SMTP_HOST'),
                string(credentialsId: 'SMTP_PORT',        variable: 'SMTP_PORT'),
                string(credentialsId: 'SMTP_USER',        variable: 'SMTP_USER'),
                string(credentialsId: 'SMTP_PASSWORD',    variable: 'SMTP_PASSWORD'),
                string(credentialsId: 'EMAIL_TO',         variable: 'EMAIL_TO')
            ]) {
                sh '''
                    python3 -m pip install requests PyYAML python-dotenv loguru jsonpath-ng
                    python3 scripts/notify_from_junit.py reports || true
                '''
            }
        }
    }
}
