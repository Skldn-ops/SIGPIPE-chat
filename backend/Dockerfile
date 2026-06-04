FROM alpine:latest

RUN apk add --no-cache python3

RUN addgroup -S siggroup && adduser -S sigusr -G siggroup

WORKDIR /app

COPY serv.py .
COPY sql_tab.py .
COPY header.py .

RUN chown -R sigusr:siggroup /app

USER sigusr

EXPOSE 8888

CMD ["python3", "./serv.py"]