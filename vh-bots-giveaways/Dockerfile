FROM vh-bots/python

WORKDIR /code

COPY ./src .

CMD [ "./wait-for-it.sh", "vh-db:8529", "--", "python", "giveaway_bot.py" ]
