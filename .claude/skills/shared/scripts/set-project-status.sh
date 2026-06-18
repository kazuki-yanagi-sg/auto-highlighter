#!/usr/bin/env bash
set -euo pipefail

# Project #18 (sky-grid-inc / senri-core-system) の issue Status を設定する。
# ボードに無ければ追加してから設定する（重複追加しない）。
# github-issue-todo / github-issue-in-progress スキル共通のヘルパー。
# usage: set-project-status.sh <issue-number> <"Todo"|"In Progress"|"Done">

OWNER="sky-grid-inc"
REPO="senri-core-system"
PROJECT_NUMBER=18

ISSUE_NUMBER="${1:?issue 番号を渡せ}"
STATUS_NAME="${2:?Status 名を渡せ（Todo / In Progress / Done）}"

ISSUE_URL="https://github.com/${OWNER}/${REPO}/issues/${ISSUE_NUMBER}"

# 既にボードに載っている item を探す
ITEM_ID=$(gh api graphql \
  -f owner="$OWNER" -f repo="$REPO" -F num="$ISSUE_NUMBER" \
  -f query='query($owner:String!,$repo:String!,$num:Int!){
    repository(owner:$owner,name:$repo){
      issue(number:$num){ projectItems(first:50){ nodes{ id project{ number } } } } } }' \
  --jq ".data.repository.issue.projectItems.nodes[] | select(.project.number==${PROJECT_NUMBER}) | .id")

# 無ければ追加
if [ -z "$ITEM_ID" ]; then
  ITEM_ID=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" --url "$ISSUE_URL" --format json --jq '.id')
fi

PROJECT_ID=$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json --jq '.id')
FIELD_ID=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json \
  --jq '.fields[] | select(.name=="Status") | .id')
OPTION_ID=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json \
  --jq ".fields[] | select(.name==\"Status\") | .options[] | select(.name==\"${STATUS_NAME}\") | .id")

if [ -z "$OPTION_ID" ]; then
  echo "Status '${STATUS_NAME}' が見つからない（Todo / In Progress / Done のいずれかを渡せ）" >&2
  exit 1
fi

gh project item-edit \
  --id "$ITEM_ID" \
  --project-id "$PROJECT_ID" \
  --field-id "$FIELD_ID" \
  --single-select-option-id "$OPTION_ID" >/dev/null

echo "issue #${ISSUE_NUMBER} → Status: ${STATUS_NAME}"
