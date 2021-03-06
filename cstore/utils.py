from django.utils.text import slugify
import random
import string
import uuid


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))




def unique_slug_generator(instance, new_slug=None):
    slug = random_string_generator(size=30)
    if new_slug is not None:
        slug = new_slug
    return slug

def store_url_slug_generator(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug

    dynamic = instance.__class__

    qs_exists = dynamic.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = "{slug}-{rndstr}".format(slug=slug, rndstr=random_string_generator(size=8))

        return unique_slug_generator(instance, new_slug=new_slug)
    return slug 


def profile_picture_upload_location(instance, filename):
    username = instance.user
    dynamic = instance.klass
    extension = filename.split(".")[-1]

    return "%s/%s/%s/%s/%s.%s" % ('users', 'profile pictures', dynamic, username, uuid.uuid4(), extension)


