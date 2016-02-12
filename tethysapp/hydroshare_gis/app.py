from tethys_sdk.base import TethysAppBase, url_map_maker


class HydroshareGis(TethysAppBase):
    """
    Tethys app class for HydroShare GIS.
    """

    name = 'HydroShare GIS'
    index = 'hydroshare_gis:home'
    icon = 'hydroshare_gis/images/icon.gif'
    package = 'hydroshare_gis'
    root_url = 'hydroshare-gis'
    color = '#1abc9c'
    description = 'View Raster and Feature Resources from HydroShare or uploaded from ' \
                  'your own computer.'
    enable_feedback = True
    feedback_emails = ['scrawley@byu.edu']

    def url_maps(self):
        """
        Add controllers
        """
        url_map = url_map_maker(self.root_url)

        url_maps = (url_map(name='home',
                            url='hydroshare-gis',
                            controller='hydroshare_gis.controllers.home'),
                    url_map(name='upload_file',
                            url='hydroshare-gis/upload-file',
                            controller='hydroshare_gis.controllers.upload_file'),
                    url_map(name='get_upload_progress',
                            url='hydroshare-gis/get-upload-progress',
                            controller='hydroshare_gis.controllers.get_upload_progress')
                    )

        return url_maps