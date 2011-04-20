
CLOUD_MEDIA_HOSTING_PROVIDERS = (
                    ('blip.tv', 'Blip.TV'      ),
                    ('default', 'Local Storage'),
)

CLOUD_MEDIA_HOSTING_BACKENDS  = {
             'blip.tv': 'cloud_media.backends.bliptv.BlipTVStorage',
             'default': 'cloud_media.backends.default.LocalStorage',
}

CLOUD_MEDIA_REMOTE_RESOURCE_CACHE_TIME = 604800 # one week.
