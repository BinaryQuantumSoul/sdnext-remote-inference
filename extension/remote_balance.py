import gradio as gr

import modules.shared

from extension.utils_remote import get_current_api_service, RemoteService, get_or_error_with_cache, get_api_key, stable_horde_client, clear_cache

balance_names = {
    RemoteService.StableHorde: ('Kudos', ''),
    RemoteService.OmniInfer: ('Credits', '$')
}

last_value = None
def remote_balance_gradio_update():
    global last_value

    value = get_remote_balance_html()

    if value != last_value:
        last_value = value

        if not value:
            return gr.HTML.update(visible=False)
        else:
            return gr.HTML.update(visible=True, value=value)
    return gr.HTML.update()

def get_remote_balance_html():
    service = get_current_api_service()
    if not modules.shared.opts.show_remote_balance or service not in balance_names.keys():
        return ''

    balance = get_remote_balance(service)
    title, symbol = balance_names[service]

    return f'<p>{title}:</p><p id="remote_inference_balance_count">{symbol}{balance}</p>'

def refresh_balance():
    service = get_current_api_service()
    if service == RemoteService:
        clear_cache(service, '/v2/find_user')
    elif service == RemoteService.OmniInfer:
        clear_cache(service, '/v3/user')

def get_remote_balance(service):
    cache_time = modules.shared.opts.remote_balance_cache_time

    if service == RemoteService.StableHorde:
        response = get_or_error_with_cache(service, '/v2/find_user', {"apikey": get_api_key(service), "Client-Agent": stable_horde_client}, cache_time)
        return int(response['kudos'])
    elif service == RemoteService.OmniInfer:
        response = get_or_error_with_cache(service, '/v3/user', {"X-Omni-Key": get_api_key(service)}, cache_time)
        return response['credit_balance']/10000.