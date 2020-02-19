FROM archlinux/base:latest
RUN pacman -Syu --needed --noconfirm \
    git \
    libffi \
    tesseract \
    openssl \
    bzip2 \
    zlib \
    readline \
    sqlite \
    fortune-mod \
    figlet \
    python-virtualenv \
    redis \
    libxslt \
    libxml2 \
    libpqxx \
    linux-api-headers \
    freetype2 \
    jpeg-archive \
    curl \
    wget \
    neofetch \
    sudo \
    gcc \
    gcc8 \
    imagemagick \
    libwebp \
    zbar \
    ffmpeg \
    procps-ng
RUN sed -e 's;^# \(%wheel.*NOPASSWD.*\);\1;g' -i /etc/sudoers
RUN useradd pagermaid -r -m -d /pagermaid
RUN usermod -aG wheel,users pagermaid
USER pagermaid
RUN mkdir /pagermaid/workdir
RUN git clone -b master https://git.stykers.moe/scm/~stykers/pagermaid.git /pagermaid/workdir
WORKDIR /pagermaid/workdir
COPY ./pagermaid.session ./config.yml /pagermaid/workdir/
RUN sudo chown pagermaid:pagermaid /pagermaid/workdir/config.yml
RUN sudo chown -f pagermaid:pagermaid /pagermaid/workdir/pagermaid.session; exit 0
RUN python3 -m virtualenv venv
RUN source venv/bin/activate; pip3 install -r requirements.txt
CMD ["sh","utils/entrypoint.sh"]
