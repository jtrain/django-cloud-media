
CLOUD_MEDIA_HOSTING_PROVIDERS = (
                    (0,         'Blip.TV'      ),
                    ('default', 'Local Storage'),
)

CLOUD_MEDIA_HOSTING_BACKENDS  = {
                     0: 'cloud_media.backends.BlipTvBackend',
             'default': 'cloud_media.backends.default.LocalStorage',
}
