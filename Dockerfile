FROM python:3.13-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/misc && chmod a+rwx /app/misc

ENV BASEDIR=/data

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]