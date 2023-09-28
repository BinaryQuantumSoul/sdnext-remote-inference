from enum import Enum
import copy
import requests
import json
import time

import modules.shared

ModelType = Enum('ModelType', ['CHECKPOINT','LORA','TEXTUALINVERSION','CONTROLNET','VAE','UPSCALER','LYCORIS','HYPERNET'])
RemoteService = Enum('RemoteService', ['Local', 'SDNext', 'StableHorde', 'OmniInfer'])
default_endpoints = {
    RemoteService.SDNext: 'http://127.0.0.1:7860',
    RemoteService.StableHorde: 'https://stablehorde.net/api',
    RemoteService.OmniInfer: 'https://api.omniinfer.io'
}
endpoint_setting_names = {
    RemoteService.SDNext: 'sdnext_api_endpoint',
    RemoteService.StableHorde: 'horde_api_endpoint',
    RemoteService.OmniInfer: 'omniinfer_api_endpoint'
}
apikey_setting_names = {
    RemoteService.StableHorde: 'horde_api_key',
    RemoteService.OmniInfer: 'omniinfer_api_key'
}

def get_remote_endpoint(remote_service):
    return modules.shared.opts.data.get(endpoint_setting_names[remote_service], default_endpoints[remote_service])

def get_api_key(remote_service):
    return modules.shared.opts.data.get(apikey_setting_names[remote_service])

def get_current_api_service():
    return RemoteService[modules.shared.opts.remote_inference_service]  

def safeget(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except (KeyError,TypeError,IndexError):
            return None
    return dct

def make_conditional_hook(func, replace_func):
    func_copy = copy.deepcopy(func)
    def wrap(*args, **kwargs):
        if get_current_api_service() == RemoteService.Local:
            return func_copy(*args, **kwargs)
        else:
            return replace_func(*args, **kwargs)
    return wrap

class RemoteInferenceError(Exception):
    def __init__(self, service, error):
        super().__init__(f'RI: error with {service} api call: {error}')

def request_or_error(service, path, headers=None, method='GET', data=None):
    try:
        response = requests.request(method=method, url=get_remote_endpoint(service)+path, headers=headers, json=data)
    except Exception as e:
        raise RemoteInferenceError(service, e)
    if response.status_code != 200:
        raise RemoteInferenceError(service, response.content)
    
    return json.loads(response.content)

cache = {}
def get_or_error_with_cache(service, path):
    global cache
    cache_key = (service, path)
    if cache_key in cache:
        result, timestamp = cache[cache_key]
        if time.time() - timestamp <= modules.shared.opts.remote_model_browser_cache_time:
            return result

    result = request_or_error(service, path)
    cache[cache_key] = (result, time.time())
    return result
