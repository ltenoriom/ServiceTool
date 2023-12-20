# Hold all the system settings in a single object
# The values are held in a configuration file

import yaml


class Config():

    def __init__(self, test_mode):
        """ Class constructor to set default values
        """
        self.test_mode = test_mode
        self.sf_url = ''
        self.request_token = ''
        self.creedentials_file = ''
        self.jira_creedentials_file = ''

    def load_file(self, file):
        """ Load the settings values

        Args:
            file (str): Settings file
        Returns:
            bool: True for success, False otherwise
        """
        ret = False

        try:
            with open(file, 'r') as stream:
                try:
                    conf_vals = yaml.safe_load(stream)
                    ret = self.parse_data(conf_vals)
                except yaml.YAMLError as exc:
                    print(exc)
        except OSError as e:
            print(e)

        return ret

    def parse_data(self, vals):
        """ Parse configuration values

        Args:
            vals(dict): Dictionary with config values
        """
        if self.test_mode:
            self.sf_url = vals['test_sf_url']
            self.request_token = vals['test_request_token']
            self.sf_creedentials_file = vals['test_sf_credentials_file']
        else:
            self.sf_url = vals['sf_url']
            self.request_token = vals['request_token']
            self.sf_creedentials_file = vals['sf_credentials_file']
        self.jira_creedentials_file = vals['jira_credentials_file']

        return True
