import sys, getopt
import configparser
import boto3
import pandas as pd


def get_profiles(profile=None, config_path='config'):
    config = configparser.RawConfigParser()
    config.read(config_path)
    config_dict = {key: dict(value) for key, value in config.items()}
    config_dict.pop('DEFAULT')
    if profile:
        return config_dict.get(profile)
    return config_dict


class EC2_Scanner:
    """
    Name:
        EC2_Scanner

    Description:
        This module provides access to ec2 scanner functions

    Attributes:
        profile (str): user profile
        region (str): ec2 instnace region
        operation (str):
        fil (str): A list of filters
        sort (str): sorting order

    Functions:
        get_instances_by_monitoring(fil)
            Return a dataframe with monitoring status of ec2 instance

        get_instances_by_state(file)
            Return a dataframe with current state of ec2 instance
    """

    def __init__(self, profile, region, operation, fil, sort):

        self.profile = profile

        self.region = region

        self.operation = operation

        self.fil = fil

        self.sort = sort

        profile = get_profiles(profile)

        try:
            self.ec2_resource = boto3.resource(
                "ec2",
                aws_access_key_id=profile.get("aws_access_key_id"),
                aws_secret_access_key=profile.get("aws_secret_access_key"),
                region_name=region,
            )
        except:
            print("Something went wrong while connecting to EC2")

    def get_instances_by_monitoring(self):

        """
            Returns the a dataframe with monitoring status of ec2 instance.

            Parameters:
                    fil (list): A list of filters

            Returns:
                    dataframe : The dataframe having two columns Instance and Monitoring
        """

        try:
            fil = self.fil

            if fil == "all":
                fil = ["enabled", "disabled"]
            else:
                value = ''  # added to remove errors, can remove this
                fil = [value]

            instances = self.ec2_resource.instances.filter(Filters=[{"Name": "monitoring-state", "Values": fil}])

            instanceId = []

            instanceMontr = []

            for instance in instances:
                instanceId.append(instance.id)

                instanceMontr.append(instance.monitoring["State"])

            data = {"Instance": instanceId, "Monitoring": instanceMontr}

            dataframe = pd.DataFrame(data)

            if len(dataframe) == 0:
                return "No Instances"

            return dataframe

        except:
            print("Something went wrong while getting ec2 instances by monitoring ")

    def get_instances_by_state(self):

        """
            Returns the a dataframe having instance id and current state  of ec2 instance.

            Parameters:
                    fil (list): A list of filters

            Returns:
                    dataframe : The dataframe having two columns Instance and State
        """
        try:
            fil = self.fil

            if fil == "all":
                fil = [
                    "pending",
                    "running",
                    "shutting-down",
                    "terminated",
                    "stopping",
                    "stopped",
                ]
            else:

                value='' # added to remove errors, can remove this
                fil = [value]

            instances = self.ec2_resource.instances.filter(Filters=[{"Name": "instance-state-name", "Values": fil}])

            instanceId = []
            instanceName = []

            for instance in instances:
                instanceId.append(instance.id)

                instanceName.append(instance.state["Name"])

            data = {"Instance": instanceId, "State": instanceName}

            dataframe = pd.DataFrame(data)

            if len(dataframe) == 0:
                return "No Instances"

            return dataframe

        except:
            print("Something went wrong while getting ec2 instances by state.")


class EBS_Scanner:
    """
    Name:
        EBS_Scanner

    Description:
        This module provides access to ebs scanner functions

    Attributes:
        profile (str): user profile
        region (str): ec2 instnace region
        operation (str):
        fil (str): A list of filters
        sort (str): sorting order

    Functions:
        get_volumes_by_state(fil)
            Return a dataframe with volume not in use of ebs

        get_volumes_by_encryption(file)
            Return a dataframe with unenrcypted volumes of ebs
    """

    def __init__(self, profile, region, operation, fil, sort):

        self.profile = profile

        self.region = region

        self.operation = operation

        self.fil = fil

        self.sort = sort

        profile = get_profiles(profile)

        try:
            self.ec2_client = boto3.client(
                "ec2",
                region_name=region,
                aws_access_key_id=profile.get("aws_access_key_id"),
                aws_secret_access_key=profile.get("aws_secret_access_key"),
            )
        except:
            print("Something went wrong while connecting to EBS")

    def get_volumes_by_state(self):

        """
            Returns the a dataframe with volume that are not in use for ebs.

            Parameters:
                    fil (list): A list of filters

            Returns:
                    dataframe : The dataframe having volumes not in use
        """
        try:
            volumes_df = pd.DataFrame()
            volume_detail = self.ec2_client.describe_volumes()

            # process each volume in volume_detail

            if volume_detail["ResponseMetadata"]["HTTPStatusCode"] == 200:

                for each_volume in volume_detail["Volumes"]:
                    volumes_df = pd.concat([volumes_df, pd.DataFrame(each_volume)])

            if len(volumes_df) == 0:
                return "No Volumes"

            if self.fil:
                return volumes_df[volumes_df["State"] == self.fil]

            return volumes_df

        except:
            print("Something went wrong while getting ebs volumes by state.")

    def get_volumes_by_encryption(self):

        """
            Returns the a dataframe with unencrypted volume of ebs.

            Parameters:
                    fil (list): A list of filters

            Returns:
                    dataframe : The dataframe having unencrypted volume
        """
        try:

            vlist = []

            response = self.ec2_client.describe_volumes()

            volumelist = response["Volumes"]

            volumns_df = pd.DataFrame(volumelist)

            if len(volumns_df) > 0:

                return volumns_df[volumns_df["Encrypted"] == False]

            else:

                return "No Volumes"
        except:
            print("Something went wrong while getting ebs volumes by encryption.")

if __name__ == '__main__':

    # get arguments from CLI
    argumentList = sys.argv[1:]
    aws_service = ''
    # check for ec2 and ebs keyword in cli
    if len(argumentList) > 0:
        aws_service = argumentList[0]
    else:
        raise Exception('Please provide arguments.')

    options = "orpfsh:"
    long_options = ["operation=", "region=", "profile=", "filter=", "sort=","help="]

    if argumentList[0] == '--help':
        if len(argumentList) == 1:
            argumentList.append("both")

        if argumentList[1] in ('ec2', 'ebs', 'both'):
            arguments, values = getopt.getopt(argumentList, options, long_options)
            for currentArgument, currentValue in arguments:
                if currentArgument in ("-h", "--help"):
                    if currentValue == "ec2":
                        help(EC2_Scanner)
                    elif currentValue == "ebs":
                        help(EBS_Scanner)
                    else:
                        help(EC2_Scanner)
                        help(EBS_Scanner)
        else:
            raise ValueError("Valid arguments --help ec2 | --help ebs | --help")

    else:
        del argumentList[0]
        if aws_service in ("ec2", "ebs"):
            arguments, values = getopt.getopt(argumentList, options, long_options)
            arguments_dict = dict(arguments)
            # considering operation,profile and region necessary args
            if '--operation' in arguments_dict and '--region' in arguments_dict and '--profile' in arguments_dict:
                method_to_call = arguments_dict.get('--operation')
                if aws_service == 'ec2':
                    ec2_scanner = EC2_Scanner(
                        arguments_dict.get('--profile'),
                        arguments_dict.get('--region'),
                        arguments_dict.get('--operation'),
                        arguments_dict.get('--filter'),
                        arguments_dict.get('--sort')
                    )
                    if method_to_call == 'state':
                        ec2_scanner.get_instances_by_state()
                    else:
                        ec2_scanner.get_instances_by_monitoring()

                elif aws_service == 'ebs':
                    ebs_scanner = EBS_Scanner(
                        arguments_dict.get('--profile'),
                        arguments_dict.get('--region'),
                        arguments_dict.get('--operation'),
                        arguments_dict.get('--filter'),
                        arguments_dict.get('--sort')
                    )
                    if method_to_call == 'state':
                        ebs_scanner.get_volumes_by_state()
                    else:
                        ebs_scanner.get_volumes_by_encryption()
            else:
                raise ValueError("Missing any argument: --operation,--region,--profile")
        else:
            raise ValueError('Missing ec2 or ebs.')
