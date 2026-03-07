// ACEest Fitness & Gym - Jenkinsfile
// Declarative Pipeline for the Jenkins BUILD phase.
// Triggered automatically by a GitHub webhook on every push to main.

pipeline {
    agent any

    environment {
        APP_NAME    = 'aceest-fitness'
        DOCKER_TAG  = "${APP_NAME}:${BUILD_NUMBER}"
        DOCKER_LATEST = "${APP_NAME}:latest"
        PYTHON_CMD  = 'python3'
    }

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        // ─────────────────────────────────────────────
        // STAGE 1 – Source Checkout
        // ─────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "Checking out source from GitHub..."
                checkout scm
                sh 'echo "Commit: $(git rev-parse --short HEAD)"'
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 2 – Environment Setup
        // ─────────────────────────────────────────────
        stage('Environment Setup') {
            steps {
                echo "Setting up Python virtual environment..."
                sh '''
                    ${PYTHON_CMD} -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    echo "Dependencies installed:"
                    pip list
                '''
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 3 – Lint & Syntax Check
        // ─────────────────────────────────────────────
        stage('Lint') {
            steps {
                echo "Running flake8 linting..."
                sh '''
                    . venv/bin/activate
                    pip install flake8 --quiet
                    flake8 app.py \
                        --count \
                        --select=E9,F63,F7,F82 \
                        --show-source \
                        --statistics
                '''
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 4 – Unit Tests (Quality Gate)
        // ─────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                echo "Running Pytest unit tests..."
                sh '''
                    . venv/bin/activate
                    pytest tests/ \
                        -v \
                        --tb=short \
                        --junitxml=test-results.xml \
                        --cov=app \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'coverage.xml',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 5 – Docker Image Build
        // ─────────────────────────────────────────────
        stage('Docker Build') {
            steps {
                echo "Building Docker image: ${DOCKER_TAG}"
                sh '''
                    docker build -t ${DOCKER_TAG} .
                    docker tag  ${DOCKER_TAG} ${DOCKER_LATEST}
                    docker images | grep aceest-fitness
                '''
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 6 – Container Smoke Test
        // ─────────────────────────────────────────────
        stage('Container Smoke Test') {
            steps {
                echo "Starting container and running health check..."
                sh '''
                    docker run -d --name aceest_build_${BUILD_NUMBER} \
                        -p 5001:5000 \
                        ${DOCKER_TAG}
                    sleep 5
                    curl --fail http://localhost:5001/health
                    docker stop aceest_build_${BUILD_NUMBER}
                    docker rm   aceest_build_${BUILD_NUMBER}
                    echo "Smoke test PASSED"
                '''
            }
        }
    }

    // ─────────────────────────────────────────────
    // POST-BUILD ACTIONS
    // ─────────────────────────────────────────────
    post {
        success {
            echo "BUILD SUCCESSFUL – ACEest v${BUILD_NUMBER} is ready."
        }
        failure {
            echo "BUILD FAILED – Check logs above for details."
            // Add Slack/email notification here if needed:
            // slackSend channel: '#devops-builds', message: "Build ${BUILD_NUMBER} FAILED"
        }
        always {
            cleanWs()   // Clean workspace after every build
        }
    }
}
