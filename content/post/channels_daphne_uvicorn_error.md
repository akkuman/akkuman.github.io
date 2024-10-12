---
title: Channels 3 Daphne Uvicorn Error AppRegistryNotReady
date: 2020-12-03 09:40:16
toc: true
tags:
- 问题解决
categories:
- 问题解决
---


Django 在使用 Channels 3 时，使用 Daphne 或者 Uvicorn 启动会出现 AppRegistryNotReady 错误

这个主要的原因是在项目启动前未初始化，我尝试自行解决了一下
<!--more-->

如果你的 asgi.py 是如下形式

```python
"""
ASGI config for homados project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from homados.middleware.wsmw import QueryXTokenAuthMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
import apps.duplex.routing
import apps.synergy.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homados.settings.dev_micro')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # Just HTTP for now. (We can add other protocols later.)
    'websocket': QueryXTokenAuthMiddleware(
        URLRouter(
            apps.duplex.routing.websocket_urlpatterns +
            apps.synergy.routing.websocket_urlpatterns
        )
    ),
})

```

那么应该是会报另外一个错误，在项目设置 `DJANGO_SETTINGS_MODULE` 前调用settings，这个错误只需要把设置环境变量前提即可

但是前提后还是会有 AppRegistryNotReady 的错误，这个错误查询了一下，[这个Issue](https://github.com/django/channels/issues/1564) 已经提出了解决方案，原因是因为django还未初始化时调用了channels路由注册，可以通过下面形式的代码来解决

```python
"""
ASGI config for homados project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homados.settings.dev_micro')

django_asgi_app = get_asgi_application()


from homados.middleware.wsmw import QueryXTokenAuthMiddleware
import apps.duplex.routing
import apps.synergy.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # Just HTTP for now. (We can add other protocols later.)
    'websocket': QueryXTokenAuthMiddleware(
        URLRouter(
            # msf 执行结果推送
            apps.duplex.routing.websocket_urlpatterns +
            # 聊天室
            apps.synergy.routing.websocket_urlpatterns
        )
    ),
})

```