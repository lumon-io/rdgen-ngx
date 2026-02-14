import io
from pathlib import Path
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core.files.base import ContentFile
import os
import re
import requests
import base64
import json
import uuid
import pyzipper
from django.conf import settings as _settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .forms import GenerateForm
from .models import GithubRun
from PIL import Image
from urllib.parse import quote
import re as _re
import logging

logger = logging.getLogger(__name__)

_UUID_PATTERN = _re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
_SAFE_FILENAME = _re.compile(r'^[a-zA-Z0-9._-]+$')


def _validate_uuid(value: str) -> str:
    """Validate and return a UUID string, or raise ValueError."""
    if not _UUID_PATTERN.match(value):
        raise ValueError(f"Invalid UUID: {value}")
    return value


def _validate_filename(value: str) -> str:
    """Validate filename has no path traversal characters."""
    basename = os.path.basename(value)
    if not basename or not _SAFE_FILENAME.match(basename):
        raise ValueError(f"Invalid filename: {value}")
    return basename


def generator_view(request):
    if request.method == 'POST':
        form = GenerateForm(request.POST, request.FILES)
        if form.is_valid():
            platform = form.cleaned_data['platform']
            version = form.cleaned_data['version']
            delayFix = form.cleaned_data['delayFix']
            cycleMonitor = form.cleaned_data['cycleMonitor']
            xOffline = form.cleaned_data['xOffline']
            hidecm = form.cleaned_data['hidecm']
            removeNewVersionNotif = form.cleaned_data['removeNewVersionNotif']
            server = form.cleaned_data['serverIP']
            key = form.cleaned_data['key']
            apiServer = form.cleaned_data['apiServer']
            urlLink = form.cleaned_data['urlLink']
            downloadLink = form.cleaned_data['downloadLink']
            if not server:
                server = 'rs-ny.rustdesk.com' #default rustdesk server
            if not key:
                key = 'OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=' #default rustdesk key
            if not apiServer:
                apiServer = server+":21114"
            if not urlLink:
                urlLink = "https://rustdesk.com"
            if not downloadLink:
                downloadLink = "https://rustdesk.com/download"
            direction = form.cleaned_data['direction']
            installation = form.cleaned_data['installation']
            settings = form.cleaned_data['settings']
            appname = form.cleaned_data['appname']
            if not appname:
                appname = "rustdesk"
            filename = form.cleaned_data['exename']
            notification_email = form.cleaned_data.get('notification_email', '')
            compname = form.cleaned_data['compname']
            if not compname:
                compname = "Purslane Ltd"
            androidappid = form.cleaned_data['androidappid']
            if not androidappid:
                androidappid = "com.carriez.flutter_hbb"
            compname = compname.replace("&","\\&")
            permPass = form.cleaned_data['permanentPassword']
            theme = form.cleaned_data['theme']
            themeDorO = form.cleaned_data['themeDorO']
            #runasadmin = form.cleaned_data['runasadmin']
            passApproveMode = form.cleaned_data['passApproveMode']
            denyLan = form.cleaned_data['denyLan']
            enableDirectIP = form.cleaned_data['enableDirectIP']
            #ipWhitelist = form.cleaned_data['ipWhitelist']
            autoClose = form.cleaned_data['autoClose']
            permissionsDorO = form.cleaned_data['permissionsDorO']
            permissionsType = form.cleaned_data['permissionsType']
            enableKeyboard = form.cleaned_data['enableKeyboard']
            enableClipboard = form.cleaned_data['enableClipboard']
            enableFileTransfer = form.cleaned_data['enableFileTransfer']
            enableAudio = form.cleaned_data['enableAudio']
            enableTCP = form.cleaned_data['enableTCP']
            enableRemoteRestart = form.cleaned_data['enableRemoteRestart']
            enableRecording = form.cleaned_data['enableRecording']
            enableBlockingInput = form.cleaned_data['enableBlockingInput']
            enableRemoteModi = form.cleaned_data['enableRemoteModi']
            removeWallpaper = form.cleaned_data['removeWallpaper']
            defaultManual = form.cleaned_data['defaultManual']
            overrideManual = form.cleaned_data['overrideManual']
            enablePrinter = form.cleaned_data['enablePrinter']
            enableCamera = form.cleaned_data['enableCamera']
            enableTerminal = form.cleaned_data['enableTerminal']

            if all(char.isascii() for char in filename):
                filename = re.sub(r'[^\w\s-]', '_', filename).strip()
                filename = filename.replace(" ","_")
            else:
                filename = "rustdesk"
            if not all(char.isascii() for char in appname):
                appname = "rustdesk"
            myuuid = str(uuid.uuid4())
            protocol = _settings.PROTOCOL
            host = request.get_host()
            full_url = f"{protocol}://{host}"
            try:
                iconfile = form.cleaned_data.get('iconfile')
                if not iconfile:
                    iconfile = form.cleaned_data.get('iconbase64')
                iconlink_url, iconlink_uuid, iconlink_file = save_png(iconfile,myuuid,full_url,"icon.png")
            except Exception:
                print("failed to get icon, using default")
                iconlink_url = "false"
                iconlink_uuid = "false"
                iconlink_file = "false"
            try:
                logofile = form.cleaned_data.get('logofile')
                if not logofile:
                    logofile = form.cleaned_data.get('logobase64')
                logolink_url, logolink_uuid, logolink_file = save_png(logofile,myuuid,full_url,"logo.png")
            except Exception:
                print("failed to get logo")
                logolink_url = "false"
                logolink_uuid = "false"
                logolink_file = "false"
            try:
                privacyfile = form.cleaned_data.get('privacyfile')
                if not privacyfile:
                    privacyfile = form.cleaned_data.get('privacybase64')
                privacylink_url, privacylink_uuid, privacylink_file = save_png(privacyfile,myuuid,full_url,"privacy.png")
            except Exception:
                print("failed to get logo")
                privacylink_url = "false"
                privacylink_uuid = "false"
                privacylink_file = "false"

            ###create the custom.txt json here and send in as inputs below
            decodedCustom = {}
            if direction != "Both":
                decodedCustom['conn-type'] = direction
            if installation == "installationN":
                decodedCustom['disable-installation'] = 'Y'
            if settings == "settingsN":
                decodedCustom['disable-settings'] = 'Y'
            if appname.upper != "rustdesk".upper and appname != "":
                decodedCustom['app-name'] = appname
            decodedCustom['override-settings'] = {}
            decodedCustom['default-settings'] = {}
            if permPass != "":
                decodedCustom['password'] = permPass
            if theme != "system":
                if themeDorO == "default":
                    if platform == "windows-x86":
                        decodedCustom['default-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
                    else:
                        decodedCustom['default-settings']['theme'] = theme
                elif themeDorO == "override":
                    if platform == "windows-x86":
                        decodedCustom['override-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
                    else:
                        decodedCustom['override-settings']['theme'] = theme
            decodedCustom['enable-lan-discovery'] = 'N' if denyLan else 'Y'
            #decodedCustom['direct-server'] = 'Y' if enableDirectIP else 'N'
            decodedCustom['allow-auto-disconnect'] = 'Y' if autoClose else 'N'
            if permissionsDorO == "default":
                decodedCustom['default-settings']['access-mode'] = permissionsType
                decodedCustom['default-settings']['enable-keyboard'] = 'Y' if enableKeyboard else 'N'
                decodedCustom['default-settings']['enable-clipboard'] = 'Y' if enableClipboard else 'N'
                decodedCustom['default-settings']['enable-file-transfer'] = 'Y' if enableFileTransfer else 'N'
                decodedCustom['default-settings']['enable-audio'] = 'Y' if enableAudio else 'N'
                decodedCustom['default-settings']['enable-tunnel'] = 'Y' if enableTCP else 'N'
                decodedCustom['default-settings']['enable-remote-restart'] = 'Y' if enableRemoteRestart else 'N'
                decodedCustom['default-settings']['enable-record-session'] = 'Y' if enableRecording else 'N'
                decodedCustom['default-settings']['enable-block-input'] = 'Y' if enableBlockingInput else 'N'
                decodedCustom['default-settings']['allow-remote-config-modification'] = 'Y' if enableRemoteModi else 'N'
                decodedCustom['default-settings']['direct-server'] = 'Y' if enableDirectIP else 'N'
                decodedCustom['default-settings']['verification-method'] = 'use-permanent-password' if hidecm else 'use-both-passwords'
                decodedCustom['default-settings']['approve-mode'] = passApproveMode
                decodedCustom['default-settings']['allow-hide-cm'] = 'Y' if hidecm else 'N'
                decodedCustom['default-settings']['allow-remove-wallpaper'] = 'Y' if removeWallpaper else 'N'
                decodedCustom['default-settings']['enable-remote-printer'] = 'Y' if enablePrinter else 'N'
                decodedCustom['default-settings']['enable-camera'] = 'Y' if enableCamera else 'N'
                decodedCustom['default-settings']['enable-terminal'] = 'Y' if enableTerminal else 'N'
            else:
                decodedCustom['override-settings']['access-mode'] = permissionsType
                decodedCustom['override-settings']['enable-keyboard'] = 'Y' if enableKeyboard else 'N'
                decodedCustom['override-settings']['enable-clipboard'] = 'Y' if enableClipboard else 'N'
                decodedCustom['override-settings']['enable-file-transfer'] = 'Y' if enableFileTransfer else 'N'
                decodedCustom['override-settings']['enable-audio'] = 'Y' if enableAudio else 'N'
                decodedCustom['override-settings']['enable-tunnel'] = 'Y' if enableTCP else 'N'
                decodedCustom['override-settings']['enable-remote-restart'] = 'Y' if enableRemoteRestart else 'N'
                decodedCustom['override-settings']['enable-record-session'] = 'Y' if enableRecording else 'N'
                decodedCustom['override-settings']['enable-block-input'] = 'Y' if enableBlockingInput else 'N'
                decodedCustom['override-settings']['allow-remote-config-modification'] = 'Y' if enableRemoteModi else 'N'
                decodedCustom['override-settings']['direct-server'] = 'Y' if enableDirectIP else 'N'
                decodedCustom['override-settings']['verification-method'] = 'use-permanent-password' if hidecm else 'use-both-passwords'
                decodedCustom['override-settings']['approve-mode'] = passApproveMode
                decodedCustom['override-settings']['allow-hide-cm'] = 'Y' if hidecm else 'N'
                decodedCustom['override-settings']['allow-remove-wallpaper'] = 'Y' if removeWallpaper else 'N'
                decodedCustom['override-settings']['enable-remote-printer'] = 'Y' if enablePrinter else 'N'
                decodedCustom['override-settings']['enable-camera'] = 'Y' if enableCamera else 'N'
                decodedCustom['override-settings']['enable-terminal'] = 'Y' if enableTerminal else 'N'

            for line in defaultManual.splitlines():
                if '=' not in line:
                    continue
                k, _, value = line.partition('=')
                decodedCustom['default-settings'][k.strip()] = value.strip()

            for line in overrideManual.splitlines():
                if '=' not in line:
                    continue
                k, _, value = line.partition('=')
                decodedCustom['override-settings'][k.strip()] = value.strip()
            
            decodedCustomJson = json.dumps(decodedCustom)

            string_bytes = decodedCustomJson.encode("ascii")
            base64_bytes = base64.b64encode(string_bytes)
            encodedCustom = base64_bytes.decode("ascii")

            # #github limits inputs to 10, so lump extras into one with json
            # extras = {}
            # extras['genurl'] = _settings.GENURL
            # #extras['runasadmin'] = runasadmin
            # extras['urlLink'] = urlLink
            # extras['downloadLink'] = downloadLink
            # extras['delayFix'] = 'true' if delayFix else 'false'
            # extras['rdgen'] = 'true'
            # extras['cycleMonitor'] = 'true' if cycleMonitor else 'false'
            # extras['xOffline'] = 'true' if xOffline else 'false'
            # extras['removeNewVersionNotif'] = 'true' if removeNewVersionNotif else 'false'
            # extras['compname'] = compname
            # extras['androidappid'] = androidappid
            # extra_input = json.dumps(extras)

            ####from here run the github action, we need user, repo, access token.
            if platform == 'windows':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows.yml/dispatches'
            if platform == 'windows-x86':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows-x86.yml/dispatches'
            elif platform == 'linux':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-linux.yml/dispatches'
            elif platform == 'android':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-android.yml/dispatches'
            elif platform == 'macos':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-macos.yml/dispatches'
            else:
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows.yml/dispatches'

            #url = 'https://api.github.com/repos/'+_settings.GHUSER+'/rustdesk/actions/workflows/test.yml/dispatches'  
            inputs_raw = {
                "server":server,
                "key":key,
                "apiServer":apiServer,
                "custom":encodedCustom,
                "uuid":myuuid,
                "iconlink_url":iconlink_url,
                "iconlink_uuid":iconlink_uuid,
                "iconlink_file":iconlink_file,
                "logolink_url":logolink_url,
                "logolink_uuid":logolink_uuid,
                "logolink_file":logolink_file,
                "privacylink_url":privacylink_url,
                "privacylink_uuid":privacylink_uuid,
                "privacylink_file":privacylink_file,
                "appname":appname,
                "genurl":_settings.GENURL,
                "urlLink":urlLink,
                "downloadLink":downloadLink,
                "delayFix": 'true' if delayFix else 'false',
                "rdgen":'true',
                "cycleMonitor": 'true' if cycleMonitor else 'false',
                "xOffline": 'true' if xOffline else 'false',
                "removeNewVersionNotif": 'true' if removeNewVersionNotif else 'false',
                "compname": compname,
                "androidappid":androidappid,
                "filename":filename
            }

            temp_json_path = f"data_{uuid.uuid4()}.json"
            zip_filename = f"secrets_{uuid.uuid4()}.zip"
            zip_path = "temp_zips/%s" % (zip_filename)
            Path("temp_zips").mkdir(parents=True, exist_ok=True)

            with open(temp_json_path, "w") as f:
                json.dump(inputs_raw, f)

            with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
                zf.setpassword(_settings.ZIP_PASSWORD.encode())
                zf.write(temp_json_path, arcname="secrets.json")

            # 4. Cleanup the plain JSON file immediately
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)

            zipJson = {}
            zipJson['url'] = full_url
            zipJson['file'] = zip_filename

            zip_url = json.dumps(zipJson)

            data = {
                "ref":_settings.GHBRANCH,
                "inputs":{
                    "version":version,
                    "zip_url":zip_url
                }
            } 
            #print(data)
            headers = {
                'Accept':  'application/vnd.github+json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+_settings.GHBEARER,
                'X-GitHub-Api-Version': '2022-11-28'
            }
            create_github_run(myuuid, email=notification_email, platform=platform, filename=filename)
            response = requests.post(url, json=data, headers=headers, timeout=30)
            print(response)
            if response.status_code == 204 or response.status_code == 200:
                return render(request, 'waiting.html', {'filename':filename, 'uuid':myuuid, 'status':"Starting generator...please wait", 'platform':platform})
            else:
                return JsonResponse({"error": "Something went wrong"})
    else:
        form = GenerateForm()
    #return render(request, 'maintenance.html')
    return render(request, 'generator.html', {'form': form})


def check_for_file(request):
    try:
        filename = _validate_filename(request.GET['filename'])
        uuid = _validate_uuid(request.GET['uuid'])
    except (KeyError, ValueError) as e:
        return HttpResponse(str(e), status=400)
    platform = request.GET['platform']
    gh_run = GithubRun.objects.filter(Q(uuid=uuid)).first()
    status = gh_run.status

    #if file_exists:
    if status == "Success":
        return render(request, 'generated.html', {'filename': filename, 'uuid':uuid, 'platform':platform})
    else:
        return render(request, 'waiting.html', {'filename':filename, 'uuid':uuid, 'status':status, 'platform':platform})

def download(request):
    try:
        filename = _validate_filename(request.GET['filename'])
        uuid = _validate_uuid(request.GET['uuid'])
    except (KeyError, ValueError) as e:
        return HttpResponse(str(e), status=400)
    file_path = os.path.join('exe', uuid, filename)
    with open(file_path, 'rb') as file:
        response = HttpResponse(file, headers={
            'Content-Type': 'application/vnd.microsoft.portable-executable',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    return response

def get_png(request):
    try:
        filename = _validate_filename(request.GET['filename'])
        uuid = _validate_uuid(request.GET['uuid'])
    except (KeyError, ValueError) as e:
        return HttpResponse(str(e), status=400)
    file_path = os.path.join('png', uuid, filename)
    with open(file_path, 'rb') as file:
        response = HttpResponse(file, headers={
            'Content-Type': 'application/vnd.microsoft.portable-executable',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    return response

def create_github_run(myuuid, email=None, platform=None, filename=None):
    new_github_run = GithubRun(
        uuid=myuuid,
        status="Starting generator...please wait",
        email=email,
        platform=platform,
        filename=filename
    )
    new_github_run.save()

@csrf_exempt
def update_github_run(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse("Invalid JSON", status=400)
    myuuid = data.get('uuid', '')
    mystatus = data.get('status', '')
    if not myuuid or not mystatus:
        return HttpResponse("Missing uuid or status", status=400)
    GithubRun.objects.filter(Q(uuid=myuuid)).update(status=mystatus)
    return HttpResponse('')

def resize_and_encode_icon(imagefile):
    maxWidth = 200
    try:
        with io.BytesIO() as image_buffer:
            for chunk in imagefile.chunks():
                image_buffer.write(chunk)
            image_buffer.seek(0)

            img = Image.open(image_buffer)
            imgcopy = img.copy()
    except (IOError, OSError):
        raise ValueError("Uploaded file is not a valid image format.")

    # Check if resizing is necessary
    if img.size[0] <= maxWidth:
        with io.BytesIO() as image_buffer:
            imgcopy.save(image_buffer, format=imagefile.content_type.split('/')[1])
            image_buffer.seek(0)
            return_image = ContentFile(image_buffer.read(), name=imagefile.name)
        return base64.b64encode(return_image.read())

    # Calculate resized height based on aspect ratio
    wpercent = (maxWidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))

    # Resize the image while maintaining aspect ratio using LANCZOS resampling
    imgcopy = imgcopy.resize((maxWidth, hsize), Image.Resampling.LANCZOS)

    with io.BytesIO() as resized_image_buffer:
        imgcopy.save(resized_image_buffer, format=imagefile.content_type.split('/')[1])
        resized_image_buffer.seek(0)

        resized_imagefile = ContentFile(resized_image_buffer.read(), name=imagefile.name)

    # Return the Base64 encoded representation of the resized image
    resized64 = base64.b64encode(resized_imagefile.read())
    #print(resized64)
    return resized64
 
#the following is used when accessed from an external source, like the rustdesk api server
@csrf_exempt
def startgh(request):
    #print(request)
    try:
        data_ = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse("Invalid JSON", status=400)
    ####from here run the github action, we need user, repo, access token.
    url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-'+data_.get('platform')+'.yml/dispatches'  
    data = {
        "ref": _settings.GHBRANCH,
        "inputs":{
            "server":data_.get('server'),
            "key":data_.get('key'),
            "apiServer":data_.get('apiServer'),
            "custom":data_.get('custom'),
            "uuid":data_.get('uuid'),
            "iconlink":data_.get('iconlink'),
            "logolink":data_.get('logolink'),
            "appname":data_.get('appname'),
            "extras":data_.get('extras'),
            "filename":data_.get('filename')
        }
    } 
    headers = {
        'Accept':  'application/vnd.github+json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+_settings.GHBEARER,
        'X-GitHub-Api-Version': '2022-11-28'
    }
    response = requests.post(url, json=data, headers=headers, timeout=30)
    print(response)
    return HttpResponse(status=204)

def save_png(file, uuid, domain, name):
    uuid = _validate_uuid(uuid)
    name = _validate_filename(name)
    file_save_path = "png/%s/%s" % (uuid, name)
    Path("png/%s" % uuid).mkdir(parents=True, exist_ok=True)

    if isinstance(file, str):  # Check if it's a base64 string
        try:
            if ';base64,' not in file:
                print("Invalid base64 data: missing ;base64, marker")
                return None
            header, encoded = file.split(';base64,', 1)
            decoded_img = base64.b64decode(encoded)
            if len(decoded_img) > 5 * 1024 * 1024:  # 5MB limit
                raise ValueError("Image too large")
            file = ContentFile(decoded_img, name=name) # Create a file-like object
        except ValueError as e:
            print(f"Invalid base64 data: {e}")
            return None  # Or handle the error as you see fit
        except Exception as e:  # Catch general exceptions during decoding
            print(f"Error decoding base64: {e}")
            return None
        
    with open(file_save_path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    # imageJson = {}
    # imageJson['url'] = domain
    # imageJson['uuid'] = uuid
    # imageJson['file'] = name
    #return "%s/%s" % (domain, file_save_path)
    return domain, uuid, name


def send_notification_email(email, uuid, filename, platform):
    """Send email notification when build completes"""
    genurl = _settings.GENURL
    subject = f'RustDesk Client Build Complete - {platform}'
    
    if platform == 'macos':
        base_name = filename.replace('.dmg', '').replace('-x86_64', '').replace('-aarch64', '')
        download_links = f"""Intel Mac: {genurl}/download?uuid={uuid}&filename={base_name}-x86_64.dmg
Apple Silicon (M1/M2/M3): {genurl}/download?uuid={uuid}&filename={base_name}-aarch64.dmg"""
    else:
        download_links = f'{genurl}/download?uuid={uuid}&filename={filename}'
    
    message = f"""Your RustDesk custom client build is complete!

Platform: {platform}

Download Links:
{download_links}

These links will expire in 24 hours.

- rdgen-ngx
"""
    
    try:
        send_mail(subject, message, _settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        print(f'Notification email sent to {email}')
    except Exception as e:
        print(f'Failed to send email: {e}')

@csrf_exempt
def save_custom_client(request):
    try:
        myuuid = _validate_uuid(request.POST.get('uuid', ''))
    except ValueError as e:
        return HttpResponse(str(e), status=400)
    file = request.FILES['file']
    safe_name = _validate_filename(file.name)
    file_save_path = os.path.join('exe', myuuid, safe_name)
    Path("exe/%s" % myuuid).mkdir(parents=True, exist_ok=True)
    with open(file_save_path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)

    # Send email notification if email was provided
    try:
        github_run = GithubRun.objects.filter(uuid=myuuid).first()
        if github_run and github_run.email:
            send_notification_email(github_run.email, myuuid, file.name, github_run.platform or 'unknown')
    except Exception as e:
        print(f'Error sending notification: {e}')
    
    return HttpResponse("File saved successfully!")

@csrf_exempt
def cleanup_secrets(request):
    # Pass the UUID as a query param or in JSON body
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse("Invalid JSON", status=400)
    my_uuid = data.get('uuid', '')

    try:
        my_uuid = _validate_uuid(my_uuid)
    except ValueError as e:
        return HttpResponse(str(e), status=400)

    # 1. Find the files in your temp directory matching the UUID
    temp_dir = os.path.join('temp_zips')

    # We look for any file starting with 'secrets_' and containing the uuid
    for filename in os.listdir(temp_dir):
        safe_filename = _validate_filename(filename)
        if my_uuid in safe_filename and safe_filename.endswith('.zip'):
            file_path = os.path.join(temp_dir, safe_filename)
            try:
                os.remove(file_path)
                print(f"Successfully deleted {file_path}")
            except OSError as e:
                print(f"Error deleting file: {e}")

    return HttpResponse("Cleanup successful", status=200)

def get_zip(request):
    try:
        filename = _validate_filename(request.GET['filename'])
    except (KeyError, ValueError) as e:
        return HttpResponse(str(e), status=400)
    file_path = os.path.join('temp_zips', filename)
    with open(file_path, 'rb') as file:
        response = HttpResponse(file, headers={
            'Content-Type': 'application/vnd.microsoft.portable-executable',
            'Content-Disposition': f'attachment; filename="{filename}"'
        })

    return response

# === rdgen-ngx ADDITIONS: Build History & Status ===

def builds_list(request):
    """Show all builds with status and download links"""
    builds = GithubRun.objects.all()[:50]  # Last 50 builds
    return render(request, 'builds_list.html', {'builds': builds})

def build_status(request, uuid):
    """Show status of a specific build"""
    try:
        uuid = _validate_uuid(uuid)
    except ValueError as e:
        return HttpResponse(str(e), status=400)
    try:
        build = GithubRun.objects.get(uuid=uuid)
    except GithubRun.DoesNotExist:
        return render(request, 'build_not_found.html', {'uuid': uuid})

    # Check if files exist
    exe_dir = f"exe/{uuid}"
    files = []
    if os.path.exists(exe_dir):
        files = os.listdir(exe_dir)
    
    return render(request, 'build_status.html', {
        'build': build,
        'files': files,
        'uuid': uuid
    })


# ============= Saved Configuration Views =============

from .models import SavedConfiguration

def list_saved_configs(request):
    """Return list of saved configuration names"""
    configs = SavedConfiguration.objects.values_list('name', flat=True)
    return JsonResponse({'configs': list(configs)})


def save_config(request):
    """Save a configuration with a name"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        name = data.get('name', '').strip()
        config_data = data.get('config', {})

        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        # Create or update
        config, created = SavedConfiguration.objects.update_or_create(
            name=name,
            defaults={'config_json': json.dumps(config_data)}
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'name': name
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def load_config(request):
    """Load a saved configuration by name"""
    name = request.GET.get('name', '')

    if not name:
        return JsonResponse({'error': 'Name parameter required'}, status=400)

    try:
        config = SavedConfiguration.objects.get(name=name)
        return JsonResponse({
            'success': True,
            'name': config.name,
            'config': json.loads(config.config_json)
        })
    except SavedConfiguration.DoesNotExist:
        return JsonResponse({'error': 'Configuration not found'}, status=404)


def delete_config(request):
    """Delete a saved configuration"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        name = data.get('name', '')

        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        deleted, _ = SavedConfiguration.objects.filter(name=name).delete()

        return JsonResponse({
            'success': deleted > 0,
            'deleted': deleted > 0
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
