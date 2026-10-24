from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def redirect_back(request, fallback, *args, **kwargs):
    """Redirect to ?next= / the previous page if it's on this site, otherwise to the fallback URL name."""
    target = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                                  require_https=request.is_secure()):
        return redirect(target)
    return redirect(fallback, *args, **kwargs)
