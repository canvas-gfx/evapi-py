import httpx
from typing import List, Optional


class EvResponseStatus:
    SUCCESS = 'success'
    ERROR = 'error'


class EvExportRange:
    ALL_PAGES = 'all_pages'
    CURRENT_PAGE = 'current_page'
    SELECTED_OBJECTS = 'selected_objects'


class EvColorMode:
    RGB = 'rgb',
    GRAYSCALE = 'grayscale'


class EvInterpolation:
    LANCZOS = 'lanczos'
    BILINEAR = 'bilinear'
    TRIANGLE = 'triangle'
    BELL = 'bell'
    BSPLINE = 'bspline'
    MITCHELL = 'mitchell'
    BICUBIC = 'bicubic'


class EvResponseError(Exception):
    def __init__(self, code, text):
        self.code = code
        self.text = text

    def __str__(self):
        err = f'Envision response error {self.code}'
        if self.text:
            err = f'{err}: {self.text}'
        return err


class EvResponse:
    def __init__(self, data: dict):
        self.data = data

    def get_type(self) -> str:
        return self.data['type']

    def get_cmd(self) -> str:
        return self.data['cmd']

    def get_status(self) -> str:
        return self.data['status']

    def get_output(self) -> dict:
        return self.data.get('data', dict())

    def get_error(self) -> EvResponseError:
        output = self.get_output()
        return EvResponseError(output['err_code'], output['err_text'])


class EvDocument:
    def __init__(self, data: dict):
        self.data = data

    def get_id(self):
        return self.data['id']


class EvPoint:
    def __init__(self, x=0, y=0):
        self.x = x,
        self.y = y


class EvSize:
    def __init__(self, w=0, h=0):
        self.w = w
        self.h = h


class EvExportOptions:
    def __init__(self,
                 page_range=EvExportRange.ALL_PAGES,
                 skip_hidden_pages=True,
                 use_objects_bounds=False,
                 create_folder=False,
                 resolution=300,
                 color_mode=EvColorMode.RGB,
                 interpolation=EvInterpolation.LANCZOS,
                 anti_alias=True):
        self.page_range = page_range
        self.skip_hidden_pages = skip_hidden_pages
        self.use_objects_bounds = use_objects_bounds
        self.create_folder = create_folder
        self.resolution = resolution
        self.color_mode = color_mode
        self.interpolation = interpolation
        self.anti_alias = anti_alias


class EvTesselationQuality:
    EXTRA_HIGH = 'extra_high',
    HIGH = 'high',
    MEDIUM = 'medium',
    LOW = 'low',
    EXTRA_LOW = 'extra_low'


class EvUnit:
    IN = 'in'
    CM = 'cm'
    PX = 'px'
    ...


class EvObject:
    def __init__(self, data):
        self.data = data

    def get_id(self):
        return self.data['id']


class EvInsert3DModelOptions:
    def __init__(self,
                 tesselation_quality=EvTesselationQuality.EXTRA_HIGH,
                 use_brep=True,
                 fit_to_page=True):
        self.tesselation_quality = tesselation_quality
        self.use_brep = use_brep
        self.fit_to_page = fit_to_page


class EvInsertVectorOptions:
    def __init__(self,
                 black_background=False,
                 ignore_line_width=False,
                 explode_autocad_hatches=False,
                 explode_autocad_blocks=False,
                 substitude_autocad_fonts_with_arial=False,
                 merge_imported_layers=False,
                 import_empty_layers=False,
                 layout_name='Layout 1',
                 layout_index=1
                 ):
        self.black_background = black_background
        self.ignore_line_width = ignore_line_width
        self.explode_autocad_hatches = explode_autocad_hatches
        self.explode_autocad_blocks = explode_autocad_blocks
        self.substitude_autocad_fonts_with_arial = substitude_autocad_fonts_with_arial
        self.merge_imported_layers = merge_imported_layers
        self.import_empty_layers = import_empty_layers
        self.layout_name = layout_name
        self.layout_index = layout_index


class EnvOptions:
    def __init__(self, units='px'):
        self.units = units


class EvApi:
    def __init__(self, host='http://localhost', port=0):
        self.host = host
        self.port = port
        self.sess = httpx.AsyncClient()

    def geturl(self):
        return f'{self.host}:{self.port}'

    def getresp(self, resp: httpx.Response) -> EvResponse:
        js = resp.json()
        evresp = EvResponse(js)
        if evresp.get_status() == EvResponseStatus.SUCCESS:
            return evresp
        elif evresp.get_status() == EvResponseStatus.ERROR:
            raise evresp.get_error()
        else:
            raise Exception(f'Got invalid response status: {evresp.get_status()}')

    async def app_set_env_options(self, env_opt: EnvOptions) -> None:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'app.set_env_options',
            'args': {
                'units': env_opt.units
            }
        })
        self.getresp(resp)

    async def debug_log(self, num_entries=20) -> List[str]:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'debug.log',
            'args': {
                'num_entries': num_entries
            }
        })
        evresp = self.getresp(resp)
        output = evresp.get_output()
        return output.get('log', [])

    async def file_open(self, path: str) -> EvDocument:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'file.open',
            'args': {
                'path': path
            }
        })
        evresp = self.getresp(resp)
        output = evresp.get_output()
        doc = output['doc']
        return EvDocument(doc)

    async def file_save(self) -> str:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'file.save',
            'args': {}
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        return output['path']

    async def file_save_as(self, path: str) -> str:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'file.save',
            'args': {
                'path': path
            }
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        return output['path']

    async def file_export(self, path: str, options: EvExportOptions) -> str:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'file.export',
            'args': {
                'path': path,
                'options': {
                    'range': options.page_range,
                    'skip_hidden_pages': options.skip_hidden_pages,
                    'use_objects_bounds': options.use_objects_bounds,
                    'create_folder': options.create_folder,
                    'resolution': options.resolution,
                    'color_mode': options.color_mode,
                    'interpolation': options.interpolation,
                    'anti_alias': options.anti_alias
                }
            }
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        return output['path']

    async def insert_3d_model(self, path: str, pos: EvPoint, size: EvSize, options: EvInsert3DModelOptions,
                              configurations: List[str], env_opt: Optional[EnvOptions] = None) -> EvObject:

        args = {
            'path': path,
            'pos': {
                'x': pos.x,
                'y': pos.y
            },
            'size': {
                'w': size.w,
                'h': size.h
            },
            'options': {
                'tesselation_quality': options.tesselation_quality,
                'use_brep': options.use_brep,
                'fit_to_page': options.fit_to_page
            },
            'configurations': configurations
        }

        if env_opt is not None:
            args['env_opt'] = {
                'units': env_opt.units
            }

        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'insert.3d_model',
            'args': args
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        obj = output['obj']
        return EvObject({'id': obj})

    async def insert_image(self, path: str, pos: EvPoint, size: EvSize,
                           env_opt: Optional[EnvOptions] = None) -> EvObject:
        args = {
            'path': path,
            'pos': {
                'x': pos.x,
                'y': pos.y
            },
            'size': {
                'w': size.w,
                'h': size.h
            }
        }

        if env_opt is not None:
            args['env_opt'] = {
                'units': env_opt.units
            }

        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'insert.image',
            'args': args
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        obj = output['obj']
        return EvObject({'id': obj})

    async def insert_vector(self, path: str, pos: EvPoint, size: EvSize, options: EvInsertVectorOptions,
                            env_opt: Optional[EnvOptions] = None) -> EvObject:
        args = {
            'path': path,
            'pos': {
                'x': pos.x,
                'y': pos.y
            },
            'size': {
                'w': size.w,
                'h': size.h
            },
            'options': {
                'black_background': options.black_background,
                'ignore_line_width': options.ignore_line_width,
                'explode_autocad_hatches': options.explode_autocad_hatches,
                'explode_autocad_blocks': options.explode_autocad_blocks,
                'substitude_autocad_fonts_with_arial': options.substitude_autocad_fonts_with_arial,
                'merge_imported_layers': options.merge_imported_layers,
                'import_empty_layers': options.import_empty_layers,
                'layout_name': options.layout_name,
                'layout_index': options.layout_index,
            }
        }

        if env_opt is not None:
            args['env_opt'] = {
                'units': env_opt.units
            }

        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'insert.vector',
            'args': args
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        obj = output['obj']
        return EvObject({'id': obj})

    async def document_name(self) -> str:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'document.name'
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        name = output['name']
        return name

    async def document_path(self) -> str:
        resp = await self.sess.post(self.geturl(), data={
            'type': 'cmd',
            'cmd': 'document.path'
        })

        evresp = self.getresp(resp)
        output = evresp.get_output()
        path = output['name']
        return path
