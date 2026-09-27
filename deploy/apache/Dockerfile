# syntax=docker/dockerfile:1
FROM node:20-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM httpd:2.4
RUN sed -i \
    -e 's/^#LoadModule ssl_module/LoadModule ssl_module/' \
    -e 's/^#LoadModule socache_shmcb_module/LoadModule socache_shmcb_module/' \
    -e 's/^#LoadModule proxy_module/LoadModule proxy_module/' \
    -e 's/^#LoadModule proxy_http_module/LoadModule proxy_http_module/' \
    -e 's/^#LoadModule headers_module/LoadModule headers_module/' \
    conf/httpd.conf \
 && printf '\nInclude conf/extra/ntma.conf\n' >> conf/httpd.conf

COPY deploy/apache/ntma.conf /usr/local/apache2/conf/extra/ntma.conf

RUN rm -rf /usr/local/apache2/htdocs/*
COPY --from=build /src/dist/ /usr/local/apache2/htdocs/
