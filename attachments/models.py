import os
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.files.storage import DefaultStorage
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
import re

# attachment storage can be customised using ATTACHMENTS_STORAGE.
storage = getattr(settings, 'ATTACHMENTS_STORAGE', None) or DefaultStorage()


class AttachmentManager(models.Manager):
    def attachments_for_object(self, obj):
        object_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=object_type.id,
                           object_id=obj.id)


class Attachment(models.Model):

    def attachment_upload(instance, filename):
        """
        Stores the attachment in a "per module/appname/primary key" folder
        """

        co = instance.content_object
        try:
            object_id = co.slug() if callable(co.slug) else co.slug
        except AttributeError:
            object_id = co.pk

        if object_id == '':
            object_id = co.pk

        extras = [
            '%s_%s' % (co._meta.app_label,
                        co._meta.object_name.lower()
            ),
            object_id]

        # slugify filename before returning its path.
        base, ext = os.path.splitext(filename.lower())
        filename = slugify(base) + ext

        fullname = 'attachments/%s/%s/%s' % (
                        tuple(extras) + (filename,))

        templates = '/%s/%s/%s'
        while len(fullname) > 100:
            try:
                extras.pop()
                templates = templates[:-3]
            except IndexError:
                break
            fullname = 'attachments' + (templates % (
                tuple(extras) + (filename,)))

        if len(fullname) > 100:
            base, ext = os.path.splitext(fullname)
            fullname = 'attachments/%s%s' % (base[:30], ext)

        return fullname

    objects = AttachmentManager()

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    creator = models.ForeignKey(User, related_name="created_attachments", verbose_name=_('creator'))
    attachment_file = models.FileField(_('attachment'),
                                 upload_to=attachment_upload, storage=storage)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    safe = models.BooleanField(_('safe'), default=False)
    mime_type = models.CharField(_('mime type'), max_length=50, null=True, blank=True,
                                 help_text=_('leave empty to handle by file extension'))
    display_name = models.CharField(_('display name'), max_length=256,
                          null=True, blank=True,
                          help_text=_('displayed as link text for attachment.'))

    class Meta:
        ordering = ['-created']
        permissions = (
            ('delete_foreign_attachments', 'Can delete foreign attachments'),
        )

    def __unicode__(self):
        return ('%s attached %s' %
                (self.creator.username,
                 self.display_name or self.attachment_file.name))

    @property
    def file_type(self):
        return self.filename.split('.')[-1]

    @property
    def link_name(self):
        return self.display_name or self.filename

    @property
    def filename(self):
        return os.path.split(self.attachment_file.name)[1]

    @property
    def nice_filename(self):
        filename = self.filename
        filename = filename.split('.')[:-1]
        filename = ' '.join(filename)
        filename = re.sub(r'[-_]', ' ', filename)
        return filename.title()



    @models.permalink
    def get_absolute_url(self):
        return ('attachments.views.retrieve_attachment', [str(self.id)])

    url = property(get_absolute_url)
