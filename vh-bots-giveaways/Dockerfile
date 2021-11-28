FROM vh-bots/python

ARG BOT_TOKEN
ENV BOT_TOKEN=${BOT_TOKEN}

WORKDIR /code

COPY ./src .

CMD ["giveaway_bot.py"]
