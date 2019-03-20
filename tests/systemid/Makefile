VERSIONS = 7.0 7.1 7.2 7.3
prepare:
	for version in ${VERSIONS} ; do \
		sed -r "s!%%PHP_VERSION%%!$$version!g;" Dockerfile.template > Dockerfile ; \
		docker build -t systemid-test-$$version . ; \
	done

test:
	for version in ${VERSIONS} ; do \
		docker run -d -p 80:80 --rm --name systemid-test-$$version-run systemid-test-$$version ; \
		sleep 2 ; \
		../../system_id_scraper.py http://127.0.0.1/phpinfo.php ; \
		docker stop systemid-test-$$version-run ; \
		sleep 2 ; \
	done
