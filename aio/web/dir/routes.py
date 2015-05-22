import os
import mimetypes
import asyncio

import aiohttp

import aio.app
import aio.http
import aio.web

from aio.core.exceptions import MissingConfiguration


@aio.web.route
def hello_world_route(request, config):
    return aiohttp.web.Response(body=b"Hello, web world")


@aio.web.fragment('aio/fragments/directory.html')
def directory_fragment(request, target):
    dir_list = os.listdir(target)

    files = {}
    file_list =  [
        os.path.basename(x)
        for x in dir_list
        if not os.path.isdir(os.path.join(target, x))]
    for f in file_list:
        files[f] = {}
        mimetype, encoding = mimetypes.guess_type(os.path.join(target, f))
        files[f]['mimetype'] = mimetype or 'application/x-octet-stream'
        files[f]['class'] = files[f]['mimetype'].replace("/", "-").replace(".", "-")

    return {
        'folders': [
            os.path.basename(x)
            for x in dir_list
            if os.path.isdir(os.path.join(target, x))],
        'files': files}


@aio.web.template('aio/directory.html')
def directory_template(request, config, target):
    header, directory_listing = yield from asyncio.gather(
        (asyncio.async(aio.web.fragments.header(request, config, title=target))),        
        (asyncio.async(directory_fragment(request, target))))
    return {
        'header': header,        
        'directory_listing': directory_listing,
        'mimetypes': mimetypes,
        'path': os.path.abspath(target)}



@aio.web.route
def directory_route(request, config=None):
    if not config.get("path", None):
        raise MissingConfiguration(
            "Section (%s) requires a path setting: %s" % (
                config.name, request.match_info.route))
    target = os.path.join(
        config['path'],
        request.match_info['path'].lstrip("/"))
    if os.path.isdir(target):
        if not request.path.endswith("/"):
            return aio.http.redirect("%s/" % request.path)
        return directory_template(request, config, target)
    elif os.path.isfile(target):
        return aio.web.filestream(request, target)
    else:
        return aiohttp.web.HTTPNotFound()
