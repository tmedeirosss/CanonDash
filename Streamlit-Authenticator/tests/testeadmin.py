import yaml

# Carregar o arquivo YAML
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)



user = config['credentials']['usernames']
role = user['31415']['role']
print(role)