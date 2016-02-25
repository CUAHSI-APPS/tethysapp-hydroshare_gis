from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from oauthlib.oauth2 import TokenExpiredError
from utilities import *
from geoserver.catalog import FailedRequestError

import shutil
from json import dumps
from StringIO import StringIO

hs_tempdir = '/tmp/hs_gis_files/'


@login_required()
def home(request):
    """
    Controller for the app home page.

    :param request: the request object sent by the browser
    """
    global engine

    engine = return_spatial_dataset_engine()

    context = {}

    return render(request, 'hydroshare_gis/home.html', context)


def load_file(request):
    """
    Controller for the "Load file from computer" button.

    :param request: the request object sent by the browser
    :returns JsonResponse: a JSON formatted response containing success value and GeoJSON object if successful
    """
    global hs_tempdir, engine
    res_id = None
    res_type = None
    res_title = None
    res_files = None
    is_zip = False

    if not os.path.exists(hs_tempdir):
        os.mkdir(hs_tempdir)

    if request.is_ajax() and request.method == 'POST':

        # Get/check files from AJAX request
        res_files = request.FILES.getlist('files')

        for res_file in res_files:
            file_name = res_file.name
            if file_name.endswith('.shp'):
                res_id = str(file_name[:-4].__hash__())
                res_type = 'GeographicFeatureResource'
                break
            elif file_name.endswith('.tif'):
                res_id = str(file_name[:-4].__hash__())
                res_type = 'RasterResource'
                res_zip = os.path.join(hs_tempdir, res_id, file_name[:-4] + '.zip')
                create_zipfile_from_file(res_file, file_name, res_zip)
                res_files = res_zip
                break
            elif file_name.endswith('.zip'):
                is_zip = True
                res_id = 'temp_id'
                res_zip = os.path.join(hs_tempdir, res_id, file_name)
                if not os.path.exists(res_zip):
                    if not os.path.exists(os.path.dirname(res_zip)):
                        os.mkdir(os.path.dirname(res_zip))
                with zipfile.ZipFile(res_zip, 'w', zipfile.ZIP_DEFLATED, False) as zip_object:
                    with zipfile.ZipFile(StringIO(res_file.read())) as z:
                        for name in z.namelist():
                            zip_object.writestr(name, z.read(name))
                            if name.endswith('.shp'):
                                res_id = str(name[:-4].__hash__())
                                res_type = 'GeographicFeatureResource'
                            elif name.endswith('.tif'):
                                res_id = str(name[:-4].__hash__())
                                res_type = 'RasterResource'
                os.rename(os.path.join(hs_tempdir, 'temp_id'), os.path.join(hs_tempdir, res_id))
                res_files = os.path.join(hs_tempdir, res_id, file_name)

    elif request.is_ajax() and request.method == 'GET':
        try:
            # CLEAR ALL OF THE GEOSERVER RESOURCES
            # stores = engine.list_stores(workspace_id)
            # for store in stores['result']:
            #     engine.delete_store(store, True, True)

            # hs = get_oauth_hs(request)
            hs = HydroShare()

            res_id = request.GET['res_id']

            if 'res_type' in request.GET:
                res_type = request.GET['res_type']
            else:
                res_type = hs.getSystemMetadata(res_id)['resource_type']

            if 'res_title' in request.GET:
                res_title = request.GET['res_title']
            else:
                res_title = hs.getSystemMetadata(res_id)['resource_title']

            store_id = 'res_%s' % res_id

            try:
                if engine.list_resources(store=store_id, debug=True)['success']:
                    # RESOURCE ALREADY STORED ON GEOSERVER
                    print 'RESOURCE ALREADY STORED ON GEOSERVER'
                    layer_name = engine.list_resources(store=store_id, debug=True)['result'][0]
                    layer_id = '%s:%s' % (workspace_id, layer_name)
                    layer_extents = get_layer_extents(res_id, layer_name, res_type)

                    return JsonResponse({
                        'success': 'Files uploaded successfully.',
                        'geoserver_url': geoserver_url,
                        'layer_name': layer_name,
                        'layer_id': layer_id,
                        'layer_extents': dumps(layer_extents)
                    })
            except FailedRequestError:
                pass
            except Exception, e:
                print e

            # RESOURCE NOT ALREADY STORED ON GEOSERVER
            hs.getResource(res_id, destination=hs_tempdir, unzip=True)
            res_contents_dir = os.path.join(hs_tempdir, res_id, res_id, 'data', 'contents')

            if os.path.exists(res_contents_dir):
                for file_name in os.listdir(res_contents_dir):
                    if file_name.endswith('.shp'):
                        res_files = os.path.join(res_contents_dir, file_name[:-4])
                    elif file_name.endswith('.tif'):
                        res_files = os.path.join(res_contents_dir, file_name[:-4] + '.zip')
                        create_zipfile_from_file(os.path.join(res_contents_dir, file_name), file_name, res_files)

        except ObjectDoesNotExist as e:
            print str(e)
            return get_json_response('error', 'Login timed out! Please re-sign in with your HydroShare account.')
        except TokenExpiredError as e:
            print str(e)
            return get_json_response('error', 'Login timed out! Please re-sign in with your HydroShare account.')
        except Exception, err:
            if "401 Unauthorized" in str(err):
                return get_json_response('error', 'Username or password invalid.')

    else:
        return get_json_response('error', 'Invalid request made.')

    layer_name, layer_id = upload_file_to_geoserver(res_id, res_type, res_files, is_zip)

    if 'res_' in layer_name:
        layer_name = res_title

    layer_extents = get_layer_extents(res_id, layer_name, res_type)

    if res_id:
        if os.path.exists(os.path.join(hs_tempdir, res_id)):
            shutil.rmtree(os.path.join(hs_tempdir, res_id))

    return JsonResponse({
        'success': 'Files uploaded successfully.',
        'geoserver_url': geoserver_url,
        'layer_name': layer_name,
        'layer_id': layer_id,
        'layer_extents': layer_extents
    })


def get_hs_res_list(request):
    if request.is_ajax() and request.method == 'GET':
        valid_res_list = []

        # hs = get_oauth_hs(request)
        hs = HydroShare()
        for resource in hs.getResourceList():
            res_type = resource['resource_type']
            if res_type == 'GeographicFeatureResource' or res_type == 'RasterResource':
                valid_res_list.append({
                    'title': resource['resource_title'],
                    'type': resource['resource_type'],
                    'id': resource['resource_id']
                })

        valid_res_json = dumps(valid_res_list)

        return JsonResponse({
            'success': 'Resources obtained successfully.',
            'resources': valid_res_json
        })
