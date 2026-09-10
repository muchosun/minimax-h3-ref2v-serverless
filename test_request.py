import unittest

from request import make_workflow


class WorkflowTests(unittest.TestCase):
    def test_photo_defaults(self):
        workflow = make_workflow('test')
        self.assertEqual(workflow['cond']['inputs']['width'], 832)
        self.assertNotIn('motion', workflow)
        self.assertEqual(workflow['sigmas']['inputs']['steps'], 20)

    def test_motion_references(self):
        workflow = make_workflow('test', 480, 864, 141, motion=True)
        self.assertEqual(workflow['cond']['inputs']['ref_videos.ref_video_0'], ['motion_frames', 0])
        self.assertEqual(workflow['motion_frames']['inputs']['video'], ['motion', 0])
        self.assertEqual(workflow['cond']['inputs']['length'], 141)
        for node in workflow.values():
            for value in node['inputs'].values():
                if isinstance(value, list):
                    self.assertIn(value[0], workflow)


if __name__ == '__main__':
    unittest.main()
