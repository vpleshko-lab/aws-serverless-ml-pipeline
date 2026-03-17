FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y mesa-libGL && dnf clean all

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# посилання на об'єкт усередині мого файлу
# handler - навза змінної, якій присвоєно Mangum (handler)
CMD ["app.app_main.handler"]
