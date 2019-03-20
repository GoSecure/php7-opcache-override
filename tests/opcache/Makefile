VERSIONS = 7.0 7.1 7.2 7.3
prepare:
	for version in ${VERSIONS} ; do \
		sed -r "s!%%PHP_VERSION%%!$$version!g;" Dockerfile.template > Dockerfile ; \
		docker build -t opcache-test-$$version . ; \
	done

test:
	for version in ${VERSIONS} ; do \
		docker run -it --rm --user 1000 -v "${CURDIR}"/opcache/:/tmp/opcache opcache-test-$$version ; \
	done
