from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from attachments.models import Attachment
from django.conf import settings
from django.template.defaultfilters import filesizeformat

ATTACHMENT_FIELDS = getattr(settings, 'ATTACHMENT_FIELDS', ('attachment_file', 'mime_type'))
ATTACHMENT_MAX_SIZE = getattr(settings, 'ATTACHMENT_MAX_SIZE', "10485760") # 10 meg


class AttachmentForm(forms.ModelForm):
    attachment_file = forms.FileField(label=_('Upload attachment'))

    class Meta:
        model = Attachment
        fields = ATTACHMENT_FIELDS

    def clean(self):
        attachment_file = self.cleaned_data['attachment_file']
        try:
            if attachment_file:
                file_type = attachment_file.content_type.split('/')[0]
                print file_type

                if len(attachment_file.name.split('.')) == 1:
                    raise forms.ValidationError(_('File type is not supported'))

                if attachment_file._size > ATTACHMENT_MAX_SIZE:
                    raise forms.ValidationError(
                        _('Please keep filesize under %s. Current filesize %s') % \
                        (filesizeformat(ATTACHMENT_MAX_SIZE), filesizeformat(attachment_file._size)))

        except:
            pass

        return self.cleaned_data

    def save(self, request, obj, *args, **kwargs):
        self.instance.creator = request.user
        self.instance.content_type = ContentType.objects.get_for_model(obj)
        self.instance.object_id = obj.id
        super(AttachmentForm, self).save(*args, **kwargs)