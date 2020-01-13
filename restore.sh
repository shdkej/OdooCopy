#/bin/bash
filename=$(ls -tr /var/lib/odoo/backups | tail -1)
dbname="test4"
BackupPath="/var/lib/odoo"
echo ${filename}
unzip ${BackupPath}/backups/${filename} -d ${BackupPath}/backups
createdb -h db -O odoo -U odoo ${dbname}
psql -h db ${dbname} -U odoo < ${BackupPath}/backups/dump.sql
mkdir ${BackupPath}/filestore/${dbname}
cp -r ${BackupPath}/filestore/* ${BackupPath}/filestore/${dbname}
