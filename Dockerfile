# syntax=docker/dockerfile:1

FROM python:3.11-slim-bullseye
WORKDIR /home/sonosantiabuse
COPY . .
RUN pip3 install -r requirements.txt
RUN groupadd --gid 1000 sonosantiabuse && \
    useradd --uid 1000 --gid 1000  --home-dir /home/sonosantiabuse --shell /bin/bash sonosantiabuse && \
    chown -R sonosantiabuse:sonosantiabuse /home/sonosantiabuse && \
    chmod +x sonos_anti_abuse.py && \
    rm requirements.txt
LABEL org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.authors="Staffan Linnaeus staffan.linnaeus@gmail.com" \
      org.opencontainers.image.description="This image is used to run the sonosantiabuse application." \
      org.opencontainers.image.created="$DATE"
USER sonosantiabuse
ENTRYPOINT ["python3", "sonos_anti_abuse.py"]
CMD ["--help"]
