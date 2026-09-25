# build telegram bot api from source
FROM debian:bookworm as build
WORKDIR /botapi
RUN apt update && apt upgrade -y && apt-get install make git zlib1g-dev libssl-dev gperf cmake g++ -y
RUN git clone --recursive https://github.com/tdlib/telegram-bot-api.git
WORKDIR /botapi/telegram-bot-api
RUN rm -rf build && mkdir build
WORKDIR /botapi/telegram-bot-api/build
RUN cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=.. .. && cmake --build . --target install

# bot
FROM python:3.11-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=build /botapi/telegram-bot-api/bin/telegram-bot-api /app/telegram-bot-api-binary
RUN chmod +x /app/telegram-bot-api-binary
EXPOSE 18081
CMD ["python", "bot.py"]