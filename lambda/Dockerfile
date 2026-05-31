FROM public.ecr.aws/lambda/python:3.13.2026.05.26.20-x86_64

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

COPY . ${LAMBDA_TASK_ROOT}

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}

CMD ["index.handler"]