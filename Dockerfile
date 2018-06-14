FROM ubuntu:xenial


RUN apt-get update && apt-get install -yq libgconf-2-4

RUN apt-get -y install curl
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get update
RUN apt-get update && apt-get install -yq libgconf-2-4 vim
RUN apt-get -y install nodejs python python-pip imagemagick redis-server git build-essential make


# Note: this installs the necessary libs to make the bundled version of Chromium that Puppeteer
RUN apt-get update && apt-get install -y wget --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-unstable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst ttf-freefont \
      --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge --auto-remove -y curl \
    && rm -rf /src/*.deb

COPY . /HookCatcher
WORKDIR /HookCatcher

RUN pip install -r requirements.txt
RUN npm install -g yarn
RUN yarn install

RUN npm i puppeteer

RUN useradd -r pptruser && chown -R pptruser . \
    && chown -R pptruser /home

USER pptruser

ENTRYPOINT ["make"]
CMD ["rundevserver"]
