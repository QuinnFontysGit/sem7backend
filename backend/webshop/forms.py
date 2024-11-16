from django import forms

class TOTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, required=True, label="One-Time Password")
