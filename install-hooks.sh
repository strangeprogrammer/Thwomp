#!/bin/bash

ln -srfT ./hooks/pre-commit ./.git/hooks/pre-commit
ln -srfT ./hooks/post-commit ./.git/hooks/post-commit
