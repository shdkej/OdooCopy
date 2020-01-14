#/bin/bash
filename=$(ls -tr | tail -5 | grep [0-9]_)
GREEN=
NC=
echo -n "${GREEN}DB명을 입력해주세요(미입력시 gvm) :${NC}"
read input
dbname="$input"
if [ -z $input ]
then
    dbname="gvm"
fi
BackupPath="/var/lib/odoo"
echo ${filename}
unzip ${filename} -d ${BackupPath}/backups
echo "${GREEN}##비밀번호를 입력해주세요 (default = myodoo)##${NC}"
createdb -h db -O odoo -U odoo ${dbname}
echo "${GREEN}##한번 더 비밀번호를 입력해주세요 (default = myodoo)##${NC}"
psql -h db -U odoo ${dbname} < ${BackupPath}/backups/dump.sql
mkdir -p ${BackupPath}/filestore/${dbname}
mv -i ${BackupPath}/backups/filestore/* ${BackupPath}/filestore/${dbname}
echo "##데이터 백업 완료##"
echo "${GREEN}소스코드 업데이트를 하시겠습니까? (y or n)${NC}"
read check_update
if [ $check_update = "n"]
then
    break
fi
git stash clear
git stash
git pull origin master
git stash drop
echo "##소스코드 업데이트 완료##"
ou analytic,gvm,gvm_mrp,hr,hr_attendance,product,project,purchase
echo "${GREEN}##데이터 업데이트 완료##${NC}"
