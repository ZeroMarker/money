sops --encrypt secrets.yaml > secrets.yaml.enc

sops --encrypt -i secrets.yaml