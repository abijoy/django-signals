from django.db import models
from django.conf import settings
from django.utils.text import slugify

from django.contrib.auth import get_user_model

# signals imports
from django.dispatch import receiver
from django.db.models.signals import (
    post_save,
    pre_save,
    pre_delete,
    post_delete,
    m2m_changed,
)

User = get_user_model()

@receiver(pre_save, sender=User)
def user_pre_save_handler(sender, instance, *args, **kwargs):
    print('------------- pre save -------------')
    print(instance.username, instance.id)


@receiver(post_save, sender=User)
def user_post_save_handler(sender, instance, created, *args, **kwargs):
    print('-------------- post save -------------')
    if created:
        print(f"Send email to {instance.username} <{instance.id}>")
    else:
        print(instance.username, 'was just saved')

# post_save.connect(user_created_handler, sender=User)


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True, null=True)
    liked = models.ManyToManyField(User, blank=True)
    notify_users = models.BooleanField(default=False)
    notify_users_timestamp = models.DateTimeField(
        blank=True, null=True, auto_now_add=False
    )
    active = models.BooleanField(default=True)


@receiver(pre_save, sender=BlogPost)
def blog_post_pre_save(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.title)

@receiver(post_save, sender=BlogPost)
def blog_post_post_save(sender, instance, created, *args, **kwargs):
    from django.utils import timezone
    if instance.notify_users:
        print("notify users")
        instance.notify_users = False
        # offload this task to Celery Background Task Manager
        instance.notify_users_timestamp = timezone.now()
        instance.save()


@receiver(pre_delete, sender=BlogPost)
def blog_post_pre_delete(sender, instance, *args, **kwargs):
    # >>> You can make a backup of this data here before deleting
    print(f'Post - {instance.id} will be deleted!')

@receiver(post_delete, sender=BlogPost)
def blog_post_post_delete(sender, instance, created, *args, **kwargs):
    print(f'Post - {instance.id} has been deleted!')



# SIGNAL FUNCTIONS FOR MANY TO MANY (m2m) 

@receiver(m2m_changed, sender=BlogPost.liked.through)
def blog_post_liked_changed(sender, instance, action, model, pk_set, *args, **kwargs):
    if action == 'pre_add':
        qs = model.objects.filter(pk__in=pk_set)
        print(f'{qs.count()} people liked')
        for q in qs: 
            print(q.username)
        