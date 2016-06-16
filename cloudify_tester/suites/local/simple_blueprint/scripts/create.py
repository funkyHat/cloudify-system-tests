#!/usr/bin/env python

import os

from cloudify import ctx


props = ctx.node.properties


def main():
    ctx.logger.info('Putting {} in {}'.format(
        props['target_file_name'],
        props['target_path'],
        ))
    os.makedirs(props['target_path'])

    ctx.download_resource(
        props['source_path'],
        os.path.join(
            props['target_path'],
            props['target_file_name']),
        )


if __name__ == "__main__":
    main()
