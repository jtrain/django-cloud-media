django-cloud-media
==================

Host your rich multimedia on cloud services. Vimeo, Youtube, Flickr backends
for videos and image galleries.

This would be useful for anyone that would like the benefits that hosting
content on a social cloud service like Vimeo brings (greater exposure to
your content). This solution allows for integration with the existing
django admin and ability to attach your media to any data type
(attach it to blog posts, cms pages, etc..). 

The goal of this project is to be able to treat your multimedia files as if
you were hosting them yourself. 


Installation
------------

1. pip install -e git://github.com/jtrain/django-cloud-media.git#egg=django-cloud-media
2. add ``'cloud_media'`` to your ``INSTALLED_APPS`` in your ``settings.py``
3. sync your database::
  
  python manage.py syncdb
4. if you use South you may migrate from a previous version.::
  
  python manage.py migrate cloud_media

Usage
-----

This app hasn't been written yet ;)

But I plan for it to be a simple process to create a multimedia model and
attach the file you wish to serve, and have the app upload the file to 
youtube or vimeo etc and store the resulting url. 

There will be template tags available to display the media. ::

  {% comment %}
    This is an example templatetag that will display a Youtube iframe or
    gallery for flickr photos depending on the media type.
  {% endcomment %}

  {% display_media obj %}


  {% comment %}
    Gets all media objects for a blog post and puts them in the current
    context.
  {% endcomment %}

  {% get_media_for obj as holiday_photos %}


