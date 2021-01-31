class Config:
    #AWS Information
    ACCESS_KEY = 'AKIAZ3KMT2WYWWJZJG5A'
    SECRET_KEY = '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'
    INSTANCE_ID = 'i-0089849b52c9845a5'
    ec2_region = "us-east-1"
    ec2_amis = ['ami-0074ee617a234808d']
    ec2_keypair = 'minecraft'
    ec2_secgroups = ['minecraft']
    ec2_instancetype = 't3.small'

    #SSH Key Path
    SSH_KEY_FILE_PATH = './minecraft.pem'

    #Server Memory Size
    #This is default to no memory specification but can be: '-Xmx1024M -Xms1024M ' (KEEP TRAILING SPACE)
    MEMORY_ALLOCATION='' 

    SERVER_PASSWORD = 'Offset-Polished-6'
