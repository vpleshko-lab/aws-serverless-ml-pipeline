FROM public.ecr.aws/lambda/python:3.12

# робоча папка проекту (DL3045)
WORKDIR ${LAMBDA_TASK_ROOT}

# залежності (тепер крапка "." точно вказує на /var/task)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код додатка
COPY app/ ./app/

# точка входу для Mangum
CMD ["app.app_main.handler"]
