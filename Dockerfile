FROM python:3.10
WORKDIR /usr/app/src
COPY . ./
RUN pip3 install websockets asyncio ipinfo
CMD ["sh","-c","echo http://localhost:8080/index.html && python legato.py table"]
